"""Bag of Baselines (Guerrero-Viu et al. 2021; card `bag-of-baselines.md`): faithful
ports of the authors' code (github.com/automl/multi-obj-baselines, BB-2 a), with the
Flowers-specific constants replaced (BB-3) and the initial sizes of BB-4.

Main track (BB-5): SHEMOA without successive halving (`shemoa.py`, one budget) and
MOBANANAS (`mobananas.py`, no SH). The multi-fidelity versions (SH-EMOA with SH,
MO-SH-BANANAS, MO-BOHB) belong to the MF track (`p3net.v005.mf`, card `mf-track.md`).

BB-3 replacements: the tournament ranks the population by NDS and hypervolume
contribution (instead of the scalar (15 - f0) f1); hypervolume in min-max normalised
objective space with reference point (1.1, 1.1) (instead of [log10(1e8), 0]);
mutation re-draws ceil(0.38 n) (SH-EMOA) / ceil(0.23 n) (MO-BANANAS) variables
(5 resp. 3 of ~13 in the source); MO-BANANAS targets are standardised (instead of
-y/10).
"""

from __future__ import annotations

import math

import numpy as np

from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import crowding_distance, fast_nondominated_sort
from p3net.v005.common import (
    EvalCache,
    cardinalities,
    initial_design_size,
    is_valid,
    online_minmax,
    random_genotype,
    space_size,
)

REF = (1.1, 1.1)
MAX_TRIES = 10_000


# ---------------------------------------------------------------------------
# Hypervolume helpers (2 objectives, minimisation)
# ---------------------------------------------------------------------------


def _hv2d(points, ref) -> float:
    pts = sorted(p for p in points if p[0] < ref[0] and p[1] < ref[1])
    hv, best_y = 0.0, ref[1]
    for x, y in pts:
        if y < best_y:
            hv += (ref[0] - x) * (best_y - y)
            best_y = y
    return hv


def _contributions(front, ref) -> list[float]:
    total = _hv2d(front, ref)
    return [total - _hv2d(front[:i] + front[i + 1:], ref) for i in range(len(front))]


def hv_contribution_remove(front) -> int:
    """SH2 (HSSP with k = |F| - 1): index of the point with the smallest
    hypervolume contribution. Reference point: 10 % of the range beyond the
    worst value of each objective."""
    front = [tuple(map(float, p)) for p in front]
    if len(front) == 1:
        return 0
    lo = [min(p[k] for p in front) for k in range(2)]
    hi = [max(p[k] for p in front) for k in range(2)]
    ref = tuple(hi[k] + 0.1 * (hi[k] - lo[k] or 1.0) for k in range(2))
    c = _contributions(front, ref)
    return int(min(range(len(front)), key=lambda i: c[i]))


def get_budgets(bmin, bmax, eta, max_evals, pop_size):
    """`shemoa.py::get_budgets` verbatim."""
    budgets = []
    b = bmax
    while b > bmin:
        budgets.append(b)
        b = math.ceil(b / eta)
    evals = []
    min_evals = math.ceil((max_evals - pop_size) / sum([eta**i for i in range(len(budgets))]))
    for _ in range(len(budgets)):
        evals.append(min_evals)
        min_evals = eta * min_evals
    return np.flip(np.array(budgets)), np.flip(np.array(evals))


# ---------------------------------------------------------------------------
# SH-EMOA operators (member.py, shemoa.py)
# ---------------------------------------------------------------------------


def _ranked(population: list[Observation]) -> list[int]:
    """BB-3: population order by NDS rank, then larger HV contribution."""
    norm = online_minmax([o.objectives for o in population])
    idx = list(range(len(population)))
    order: list[int] = []
    for front in fast_nondominated_sort(idx, lambda i: tuple(population[i].objectives)):
        pts = [norm(population[i].objectives) for i in front]
        c = _contributions(pts, REF)
        order.extend(i for _, i in sorted(zip([-x for x in c], front)))
    return order


def shemoa_tournament(population: list[Observation], k: int, rng) -> Observation:
    """Tournament of k (without replacement) over the ranked population: the
    member with the best position wins (`select_parents`, TOURNAMENT)."""
    order = _ranked(population)
    pos = {i: r for r, i in enumerate(order)}
    sample = rng.sample(range(len(population)), min(k, len(population)))
    return population[min(sample, key=lambda i: pos[i])]


def uniform_crossover(p1: Genotype, p2: Genotype, rng, recom_prob: float = 0.5) -> Genotype:
    """`Member.recombine` UNIFORM: each gene from the partner iff rand >= recom_prob."""
    return Genotype(values=tuple(b if rng.random() >= recom_prob else a for a, b in zip(p1.values, p2.values)))


def shemoa_mutation(g: Genotype, domains, n_mut: int, rng) -> Genotype:
    """`Member.mutate` UNIFORM: n_mut distinct variables re-drawn uniformly."""
    out = list(g.values)
    for i in rng.sample(range(len(domains)), min(n_mut, len(domains))):
        out[i] = rng.randrange(domains[i])
    return Genotype(values=tuple(out))


class SHEMOA:
    """Steady-state EMOA of `shemoa.py` with a single budget (main track, BB-5)."""

    def __init__(self, space, budget, rng, *, population_size: int = 20, fraction_mutation: float = 0.5,
                 tournament_k: int = 3):
        self.space, self.rng, self.budget = space, rng, int(budget)
        self.domains = cardinalities(space)
        self.pop_size = initial_design_size(population_size, self.budget)
        self.frac_mut, self.k = fraction_mutation, tournament_k
        self.n_mut = math.ceil(0.38 * len(self.domains))
        self.cache = EvalCache()
        self.population: list[Observation] = []
        self.used = 0
        self._pending: list[Genotype] = []
        self._size = space_size(space)

    def config(self) -> dict:
        return {"population_size": self.pop_size, "fraction_mutation": self.frac_mut, "tournament_k": self.k,
                "n_mut": self.n_mut, "recom_prob": 0.5, "successive_halving": False}

    def _child(self) -> Genotype | None:
        for _ in range(MAX_TRIES):
            parent = shemoa_tournament(self.population, self.k, self.rng)
            if self.rng.random() < self.frac_mut:
                c = shemoa_mutation(parent.genotype, self.domains, self.n_mut, self.rng)
            else:
                partner = self.rng.choice(self.population)
                c = uniform_crossover(parent.genotype, partner.genotype, self.rng)
            if c not in self.cache and is_valid(self.space, c):
                return c
            if len(self.cache) >= self._size:
                return None
        return None

    def propose(self, state: RunState) -> list[Genotype]:
        remaining = self.budget - self.used
        if remaining <= 0 or self._pending:
            return []
        if not self.population:
            batch: list[Genotype] = []
            while len(batch) < min(self.pop_size, remaining):
                g = random_genotype(self.space, self.rng)
                if g not in batch:
                    batch.append(g)
        else:
            c = self._child()
            batch = [c] if c is not None else []
        self._pending = batch
        self.used += len(batch)
        return list(batch)

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        new = []
        for obs in new_observations:
            self.cache.put(obs.genotype, obs.objectives)
            new.append(Observation(genotype=obs.genotype, objectives=tuple(obs.objectives)))
        if not self.population:
            self.population = new
        else:
            pop = self.population + new
            idx = list(range(len(pop)))
            last = fast_nondominated_sort(idx, lambda i: tuple(pop[i].objectives))[-1]
            norm = online_minmax([o.objectives for o in pop])
            if len(last) == 1:
                drop = last[0]
            else:
                drop = last[hv_contribution_remove([norm(pop[i].objectives) for i in last])]
            self.population = [o for i, o in enumerate(pop) if i != drop]
        self._pending = []


# ---------------------------------------------------------------------------
# MO-BANANAS (mobananas.py, neural_predictor.py)
# ---------------------------------------------------------------------------


class _Net:
    """`neural_predictor.Net`: Linear(n, 10) -> ReLU -> Linear(10, 2), normal init,
    MSE, Adam lr 0.1, batch 32."""

    def __init__(self, n_in: int, npr):
        self.W1, self.b1 = npr.standard_normal((n_in, 10)), npr.standard_normal(10)
        self.W2, self.b2 = npr.standard_normal((10, 2)), npr.standard_normal(2)
        self.npr = npr
        self._m = [np.zeros_like(p) for p in self._params()]
        self._v = [np.zeros_like(p) for p in self._params()]
        self._t = 0

    def _params(self):
        return [self.W1, self.b1, self.W2, self.b2]

    def forward(self, X):
        h = X @ self.W1 + self.b1
        return np.maximum(h, 0.0) @ self.W2 + self.b2, h

    def train(self, X, Y, epochs: int, lr: float = 0.1, batch: int = 32):
        for _ in range(epochs):
            idx = self.npr.permutation(len(X))
            for s in range(0, len(X), batch):
                b = idx[s:s + batch]
                x, y = X[b], Y[b]
                out, h = self.forward(x)
                g_out = 2.0 * (out - y) / out.size  # d MSE / d out
                a = np.maximum(h, 0.0)
                gW2, gb2 = a.T @ g_out, g_out.sum(0)
                g_h = (g_out @ self.W2.T) * (h > 0)
                gW1, gb1 = x.T @ g_h, g_h.sum(0)
                self._t += 1
                for p, g, m, v in zip(self._params(), [gW1, gb1, gW2, gb2], self._m, self._v):
                    m *= 0.9
                    m += 0.1 * g
                    v *= 0.999
                    v += 0.001 * g * g
                    p -= lr * (m / (1 - 0.9**self._t)) / (np.sqrt(v / (1 - 0.999**self._t)) + 1e-8)

    def predict(self, X):
        return self.forward(X)[0]


def _sort_positions(fit) -> list[int]:
    """`neural_predictor.sort_array`: position of every point in the NDS + crowding order."""
    idx = list(range(len(fit)))
    order: list[int] = []
    for front in fast_nondominated_sort(idx, lambda i: tuple(fit[i])):
        cd = crowding_distance(front, lambda i: tuple(fit[i]))
        order.extend(front[k] for k in sorted(range(len(front)), key=lambda k: -cd[k]))
    return [order.index(i) for i in range(len(fit))]


class MOBANANAS:
    """`mobananas.py::BANANAS` without successive halving (main track, BB-5)."""

    def __init__(self, space, budget, rng, *, initial_samples: int = 20, num_arch: int = 8, select_models: int = 4,
                 ensemble_size: int = 5, epochs: int = 80):
        self.space, self.rng, self.budget = space, rng, int(budget)
        self.domains = cardinalities(space)
        self.n_init = initial_design_size(initial_samples, self.budget)
        self.num_arch, self.select = int(num_arch), int(select_models)
        self.ensemble_size, self.epochs = int(ensemble_size), int(epochs)
        self.n_mut = math.ceil(0.23 * len(self.domains))
        self.npr = np.random.default_rng(rng.getrandbits(64))
        self.cache = EvalCache()
        self.used = 0
        self._pending: list[Genotype] = []

    def config(self) -> dict:
        return {"initial_samples": self.n_init, "num_arch": self.num_arch, "select_models": self.select,
                "ensemble_size": self.ensemble_size, "epochs": self.epochs, "lr": 0.1, "loss": "mse",
                "target_scaling": "standardize", "n_mut": self.n_mut, "successive_halving": False}

    def _x(self, gs) -> np.ndarray:
        return np.array([[v / max(1, k - 1) for v, k in zip(g.values, self.domains)] for g in gs], dtype=float)

    def _mutate(self, g: Genotype) -> Genotype:
        return shemoa_mutation(g, self.domains, self.n_mut, self.rng)  # categorical: re-drawn (`except` branch)

    def _iteration(self, k: int) -> list[Genotype]:
        hist = self.cache.history()
        X = self._x([o.genotype for o in hist])
        Y = np.array([o.objectives for o in hist], dtype=float)
        mu, sd = Y.mean(0), Y.std(0)
        sd[sd == 0] = 1.0
        nets = [_Net(X.shape[1], self.npr) for _ in range(self.ensemble_size)]
        for net in nets:
            net.train(X, (Y - mu) / sd, self.epochs)
        pos = _sort_positions([tuple(o.objectives) for o in hist])
        best = [hist[i] for i in sorted(range(len(hist)), key=lambda i: pos[i])[: self.num_arch]]
        cands: list[Genotype] = []
        for parent in best:
            for _ in range(MAX_TRIES):
                c = self._mutate(parent.genotype)
                if c not in self.cache and c not in cands and is_valid(self.space, c):
                    cands.append(c)
                    break
        while len(cands) < k:  # too few unique mutants (tiny spaces): random fill
            g = random_genotype(self.space, self.rng)
            if g not in self.cache and g not in cands:
                cands.append(g)
        Xc = self._x(cands)
        preds = [net.predict(Xc) * sd + mu for net in nets]  # per model, per candidate
        mean = np.mean(preds, axis=0)
        mean_pos = _sort_positions([tuple(m) for m in mean])
        model_pos = [_sort_positions([tuple(p) for p in pr]) for pr in preds]
        M = self.ensemble_size
        probs = []
        for i in range(len(cands)):  # independent_thompson_sampling on positions
            sq = sum((abs(model_pos[m][i]) - mean_pos[i]) ** 2 for m in range(M))
            probs.append(self.npr.normal(mean_pos[i], math.sqrt(sq / (M - 1))))
        order = sorted(range(len(cands)), key=lambda i: probs[i])
        return [cands[i] for i in order[:k]]

    def propose(self, state: RunState) -> list[Genotype]:
        remaining = self.budget - self.used
        if remaining <= 0 or self._pending:
            return []
        if len(self.cache) == 0:
            batch: list[Genotype] = []
            while len(batch) < min(self.n_init, remaining):
                g = random_genotype(self.space, self.rng)
                if g not in batch:
                    batch.append(g)
        else:
            batch = self._iteration(min(self.select, remaining))
        self._pending = batch
        self.used += len(batch)
        return list(batch)

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(obs.genotype, obs.objectives)
        self._pending = []


def __getattr__(name: str):
    """MF-track classes live in p3net.v005.mf; re-exported here for the card's naming."""
    if name in ("MOSHBANANAS", "MOBOHB", "SHEMOAMF"):
        from p3net.v005 import mf

        return getattr(mf, name)
    raise AttributeError(name)
