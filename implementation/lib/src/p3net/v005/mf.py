"""Multi-fidelity track (card `mf-track.md`, MF-1 a ... MF-4).

Ask-tell protocol (interfaces §7, Q-31): methods take `max_epochs` (E); `propose`
returns (genotype, epochs) pairs; answers come back as Observations in the same
order; `final_observations()` returns the evaluations at e = E, the only ones that
enter fronts and metrics.

- Cost (§2): a query (g, e) after e_prev epochs of g costs (e - e_prev) / E; a query
  that would exceed the budget is not made (K-2).
- f2 at e < E (MF-1 a): the observed e-epoch value; promotion uses the extrapolation
  per-epoch cost x E.
- Hyperband (Li et al. 2018, Alg. 1) and ASHA (Li et al. 2020, Alg. 2) with the
  NSGA-II promotion of MO-ASHA (Schmucker et al. 2021; MF-2 a), eta = 3, r_min = 1
  epoch (MF-3).
"""

from __future__ import annotations

import math

from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import crowding_distance, fast_nondominated_sort
from p3net.v005.common import cardinalities, random_genotype


def mf_cost(e: int, e_prev: int, E: int) -> float:
    return max(0, int(e) - int(e_prev)) / float(E)


def extrapolate_f2(f2_at_e: float, e: int, E: int) -> float:
    """MF-1 a: per-epoch cost observed after e epochs, times E."""
    return float(f2_at_e) * float(E) / float(e)


def bracket_schedule(eta: int, r_min: int, R: int) -> list[list[tuple[int, int]]]:
    """Li et al. 2018, Alg. 1: brackets s = s_max ... 0; bracket s starts with
    n = ceil((s_max+1)/(s+1) eta^s) configurations at r = R eta^-s; rung i has
    floor(n eta^-i) configurations at r eta^i epochs (rounded to whole epochs)."""
    s_max = 0
    while r_min * eta ** (s_max + 1) <= R:
        s_max += 1
    out = []
    for s in range(s_max, -1, -1):
        n = math.ceil((s_max + 1) / (s + 1) * eta**s)
        r = R / eta**s
        out.append([(math.floor(n / eta**i), max(1, round(r * eta**i))) for i in range(s + 1)])
    return out


def _fronts_2d(points):
    """Non-dominated fronts of two-objective points (minimised) by a sweep in f1 order,
    O(n * #fronts) instead of O(n^2): a point joins the first front whose last member
    does not dominate it. Same fronts as `fast_nondominated_sort`, each sorted by index."""
    order = sorted(range(len(points)), key=lambda i: (points[i][0], points[i][1], i))
    fronts: list[list[int]] = []
    for i in order:
        a1, a2 = points[i][0], points[i][1]
        for front in fronts:
            b1, b2 = points[front[-1]][0], points[front[-1]][1]
            if not (b1 <= a1 and b2 <= a2 and (b1 < a1 or b2 < a2)):
                front.append(i)
                break
        else:
            fronts.append([i])
    return [sorted(f) for f in fronts]


def promote_nsga2(points, k: int) -> list[int]:
    """MF-2 a: indices of the first k points by (NDS rank, -crowding distance)."""
    idx = list(range(len(points)))
    order: list[int] = []
    two = bool(points) and all(len(p) == 2 for p in points)
    fronts = _fronts_2d(points) if two else fast_nondominated_sort(idx, lambda i: tuple(points[i]))
    for front in fronts:
        cd = crowding_distance(front, lambda i: tuple(points[i]))
        order.extend(front[j] for j in sorted(range(len(front)), key=lambda j: -cd[j]))
        if len(order) >= k:
            break
    return order[:k]


class _MFBase:
    def __init__(self, space, budget, rng, *, max_epochs: int, eta: int = 3, r_min: int = 1):
        self.space, self.rng, self.budget = space, rng, float(budget)
        self.E, self.eta, self.r_min = int(max_epochs), int(eta), int(r_min)
        self.domains = cardinalities(space)
        self.spent = 0.0
        self.last: dict[Genotype, int] = {}  # epochs already trained per genotype
        self.results: dict[tuple[Genotype, int], tuple[float, ...]] = {}
        self.sampled: set[Genotype] = set()
        self._pending: list[tuple[Genotype, int]] = []
        self.stop_reason: str | None = None

    def config(self) -> dict:
        return {"max_epochs": self.E, "eta": self.eta, "r_min": self.r_min, "promotion": "nsga2"}

    def _new_config(self) -> Genotype:
        for _ in range(100_000):
            g = random_genotype(self.space, self.rng)
            if g not in self.sampled:
                self.sampled.add(g)
                return g
        raise RuntimeError("search space exhausted")

    def _affordable(self, queries: list[tuple[Genotype, int]]) -> list[tuple[Genotype, int]]:
        """K-2: keep queries in order while their total cost fits the budget."""
        out, spent, last = [], self.spent, dict(self.last)
        for g, e in queries:
            c = mf_cost(e, last.get(g, 0), self.E)
            if spent + c > self.budget + 1e-9:
                self.stop_reason = "budget exhausted"
                break
            spent += c
            last[g] = max(last.get(g, 0), e)
            out.append((g, e))
        return out

    def _score(self, g: Genotype, e: int) -> tuple[float, float]:
        f1, f2 = self.results[(g, e)][:2]
        return (f1, extrapolate_f2(f2, e, self.E))  # MF-1 a

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for (g, e), obs in zip(self._pending, new_observations):
            self.spent += mf_cost(e, self.last.get(g, 0), self.E)
            self.last[g] = max(self.last.get(g, 0), e)
            self.results[(g, e)] = tuple(float(x) for x in obs.objectives)
        self._pending = []

    def final_observations(self) -> list[Observation]:
        return [Observation(genotype=g, objectives=o) for (g, e), o in self.results.items() if e == self.E]


class HyperbandMO(_MFBase):
    """Hyperband brackets in order s_max ... 0, then cyclically; new configurations
    at random; promotion by NDS + crowding (MO-ASHA's NSGA-II variant)."""

    def __init__(self, space, budget, rng, *, max_epochs: int, eta: int = 3, r_min: int = 1):
        super().__init__(space, budget, rng, max_epochs=max_epochs, eta=eta, r_min=r_min)
        self.schedule = bracket_schedule(self.eta, self.r_min, self.E)
        self._bracket = 0
        self._rung = 0
        self._configs: list[Genotype] = []

    def propose(self, state: RunState) -> list[tuple[Genotype, int]]:
        if self.stop_reason is not None or self._pending:
            return []
        rungs = self.schedule[self._bracket % len(self.schedule)]
        if self._rung == 0:
            self._configs = [self._new_config() for _ in range(rungs[0][0])]
        else:
            prev_e = rungs[self._rung - 1][1]
            pts = [self._score(g, prev_e) for g in self._configs]
            keep = promote_nsga2(pts, rungs[self._rung][0])
            self._configs = [self._configs[i] for i in keep]
        e = rungs[self._rung][1]
        batch = self._affordable([(g, e) for g in self._configs])
        self._configs = [g for g, _ in batch] if len(batch) < len(self._configs) else self._configs
        self._rung += 1
        if self._rung >= len(rungs):
            self._bracket, self._rung = self._bracket + 1, 0
        self._pending = batch
        return list(batch)


class ASHAMO(_MFBase):
    """ASHA with one worker (Li et al. 2020, Alg. 2): promote from the highest rung
    with a not yet promoted configuration among its top floor(n_k / eta); otherwise
    start a new configuration at the bottom rung. Rung epochs = the largest
    Hyperband bracket."""

    def __init__(self, space, budget, rng, *, max_epochs: int, eta: int = 3, r_min: int = 1):
        super().__init__(space, budget, rng, max_epochs=max_epochs, eta=eta, r_min=r_min)
        self.ladder = [r for _, r in bracket_schedule(self.eta, self.r_min, self.E)[0]]
        self.rungs: list[list[Genotype]] = [[] for _ in self.ladder]
        self.promoted: list[set[Genotype]] = [set() for _ in self.ladder]

    def _job(self) -> tuple[Genotype, int]:
        for k in range(len(self.ladder) - 2, -1, -1):
            members = self.rungs[k]
            n_top = len(members) // self.eta
            if n_top == 0:
                continue
            pts = [self._score(g, self.ladder[k]) for g in members]
            for i in promote_nsga2(pts, n_top):
                g = members[i]
                if g not in self.promoted[k]:
                    self.promoted[k].add(g)
                    return g, self.ladder[k + 1]
        return self._new_config(), self.ladder[0]

    def propose(self, state: RunState) -> list[tuple[Genotype, int]]:
        if self.stop_reason is not None or self._pending:
            return []
        batch = self._affordable([self._job()])
        self._pending = batch
        return list(batch)

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for g, e in self._pending:
            self.rungs[self.ladder.index(e)].append(g)
        super().update(state, new_observations)


class _MFGenerator(_MFBase):
    """MF method written as a generator: `_run` yields batches of (genotype, epochs)
    and receives their objectives; queries already answered come from the results
    (#35); a batch that does not fit the budget is cut and the run ends (K-2)."""

    def __init__(self, space, budget, rng, *, max_epochs: int, eta: int):
        super().__init__(space, budget, rng, max_epochs=max_epochs, eta=eta)
        self._gen = None
        self._batch: list[tuple[Genotype, int]] = []
        self._answers: dict[tuple[Genotype, int], tuple[float, ...]] = {}

    def _run(self):
        raise NotImplementedError

    def propose(self, state: RunState) -> list[tuple[Genotype, int]]:
        if self.stop_reason is not None or self._pending:
            return []
        if self._gen is None:
            self._gen = self._run()
            msg = None
        else:
            msg = [self.results[q] for q in self._batch]
        while True:
            try:
                self._batch = list(self._gen.send(msg) if msg is not None else next(self._gen))
            except StopIteration:
                self.stop_reason = "algorithm finished"
                return []
            todo = list(dict.fromkeys(q for q in self._batch if q not in self.results))
            if not todo:
                msg = [self.results[q] for q in self._batch]
                continue
            batch = self._affordable(todo)
            if not batch:
                return []
            self._pending = batch
            return list(batch)


class SHEMOAMF(_MFGenerator):
    """SH-EMOA with successive halving (`shemoa.py`; MF-3 a: b_min = ceil(0.2 E),
    b_max = E, eta = 2; MF-4: population min(20, floor(0.25 b))). The number of
    function evaluations of `get_budgets` is the largest whose planned cost (with
    resumed training when the population moves to a larger budget) fits the budget."""

    def __init__(self, space, budget, rng, *, max_epochs: int):
        super().__init__(space, budget, rng, max_epochs=max_epochs, eta=2)
        from p3net.v005.baselines.bob import get_budgets, initial_design_size

        self.pop_size = initial_design_size(20, int(budget))
        b_min = math.ceil(0.2 * self.E)
        self.n_mut = math.ceil(0.38 * len(self.domains))
        best = None
        for fe in range(self.pop_size + 1, 100_000):
            budgets, evals = get_budgets(b_min, self.E, self.eta, fe, self.pop_size)
            if self._planned_cost(budgets, evals) > self.budget:
                break
            best = (budgets, evals)
        self.budgets, self.evals = best if best is not None else get_budgets(b_min, self.E, self.eta,
                                                                             self.pop_size + 1, self.pop_size)

    def _planned_cost(self, budgets, evals) -> float:
        cost = self.pop_size * budgets[0] / self.E
        for i, b in enumerate(budgets):
            if i > 0:
                cost += self.pop_size * (b - budgets[i - 1]) / self.E
            cost += evals[i] * b / self.E
        return cost

    def config(self) -> dict:
        return {**super().config(), "budgets": [int(b) for b in self.budgets], "evals": [int(e) for e in self.evals],
                "population": self.pop_size}

    def _run(self):
        from p3net.v005.baselines.bob import hv_contribution_remove, shemoa_mutation, shemoa_tournament, uniform_crossover
        from p3net.v005.common import online_minmax

        pop = [self._new_config() for _ in range(self.pop_size)]
        for level, (b, n_steps) in enumerate(zip(self.budgets, self.evals)):
            b = int(b)
            objs = yield [(g, b) for g in pop]  # SH3: the population (re-)evaluated at this budget
            members = [Observation(genotype=g, objectives=tuple(o)) for g, o in zip(pop, objs)]
            for _ in range(int(n_steps)):
                for _ in range(10_000):
                    parent = shemoa_tournament(members, 3, self.rng)
                    if self.rng.random() < 0.5:
                        child = shemoa_mutation(parent.genotype, self.domains, self.n_mut, self.rng)
                    else:
                        child = uniform_crossover(parent.genotype, self.rng.choice(members).genotype, self.rng)
                    if (child, b) not in self.results and all(child != m.genotype for m in members):
                        break
                (f,) = yield [(child, b)]
                members.append(Observation(genotype=child, objectives=tuple(f)))
                idx = list(range(len(members)))
                last = fast_nondominated_sort(idx, lambda i: tuple(members[i].objectives))[-1]
                norm = online_minmax([m.objectives for m in members])
                drop = last[0] if len(last) == 1 else last[hv_contribution_remove([norm(members[i].objectives)
                                                                                   for i in last])]
                members = [m for i, m in enumerate(members) if i != drop]
            pop = [m.genotype for m in members]


class MOSHBANANAS(_MFGenerator):
    """MO-SH-BANANAS (`moshbananas.py`): MO-BANANAS whose `select` candidates go
    through successive halving (eta = 3) on the ladder of `get_budgets(b_min, E, 3)`
    in ascending order, keeping len // eta by NDS + crowding after each rung; the
    survivors join the architecture list. Initial architectures at E. Settings of the
    source example (initial 10, num_arch 20, select 10) with MF-3 a b_min = ceil(0.2 E)."""

    def __init__(self, space, budget, rng, *, max_epochs: int, initial_samples: int = 10, num_arch: int = 20,
                 select_models: int = 10):
        super().__init__(space, budget, rng, max_epochs=max_epochs, eta=3)
        from p3net.v005.common import initial_design_size

        self.n_init = max(2, initial_design_size(initial_samples, int(budget)))
        self.num_arch, self.select = int(num_arch), int(select_models)
        b, ladder = self.E, []
        while b > math.ceil(0.2 * self.E):
            ladder.append(b)
            b = math.ceil(b / self.eta)
        self.ladder = ladder[::-1]

    def config(self) -> dict:
        return {**super().config(), "initial_samples": self.n_init, "num_arch": self.num_arch,
                "select_models": self.select, "ladder": self.ladder}

    def _run(self):
        import numpy as np

        from p3net.v005.baselines.bob import MOBANANAS, _sort_positions

        inner = MOBANANAS(self.space, 10**9, self.rng)  # reuse predictor, mutation and Thompson selection
        inner.num_arch, inner.select = self.num_arch, self.select
        archs = [self._new_config() for _ in range(self.n_init)]
        objs = yield [(g, self.E) for g in archs]
        for g, o in zip(archs, objs):
            inner.cache.put(g, o)
        while True:
            chosen = inner._iteration(self.select)
            for g in chosen:
                self.sampled.add(g)
            members = list(chosen)
            last_objs: list = []
            for b in self.ladder:
                if not members:
                    break
                last_objs = yield [(g, b) for g in members]
                pos = _sort_positions([tuple(o) for o in last_objs])
                order = sorted(range(len(members)), key=lambda i: pos[i])
                keep = order[: len(members) // self.eta]
                survivors = [(members[i], last_objs[i]) for i in keep]
                members = [g for g, _ in survivors]
                last_objs = [o for _, o in survivors]
            for g, o in zip(members, last_objs):
                inner.cache.put(g, o)
            if not members and len(inner.cache) == 0:
                return
            _ = np  # keep the import local to the method


_EPS = 2.220446049250313e-16  # sys.float_info.epsilon, as in mobohb_utils


def _nds_ranks(points):
    """`mobohb_utils.nondominated_sort`."""
    import numpy as np

    points = np.array(points, dtype=float)
    ranks = np.zeros(len(points))
    used = np.zeros(len(points), dtype=bool)
    r = 0
    while not used.all():
        idx = [i for i in range(len(points)) if not used[i]]
        front = [i for i in idx if not any(np.all(points[j] <= points[i]) and np.any(points[j] < points[i])
                                           for j in idx if j != i)]
        for i in front:
            ranks[i], used[i] = r, True
        r += 1
    return ranks


def _hv(points, ref) -> float:
    from p3net.v005.baselines.bob import _hv2d

    return _hv2d([tuple(p) for p in points], tuple(ref))


def _motpe_split(ys, n_lower):
    """`TPESampler._split_observations`: whole fronts while they fit, then a greedy
    hypervolume selection inside the next front (pygmo hypervolume -> 2-D HV)."""
    import numpy as np

    ys = np.asarray(ys, dtype=float)
    rank = _nds_ranks(ys)
    indices = np.arange(len(ys))
    lower = np.array([], dtype=int)
    i = 0
    while len(lower) + int(np.sum(rank == i)) <= n_lower:
        lower = np.append(lower, indices[rank == i])
        i += 1
    ys_r, idx_r = ys[rank == i], indices[rank == i]
    worst = np.max(ys, axis=0)
    ref = np.maximum(np.maximum(1.1 * worst, 0.9 * worst), np.full(len(worst), _EPS))
    S: list = []
    contrib = [_hv([y], ref) for y in ys_r]
    while len(lower) + 1 <= n_lower:
        hv_S = _hv(S, ref) if S else 0.0
        k = int(np.argmax(contrib))
        contrib[k] = -1e9
        for j in range(len(contrib)):
            if j != k:
                p_q = np.max([ys_r[k], ys_r[j]], axis=0)
                contrib[j] -= _hv(S + [p_q], ref) - hv_S
        S.append(ys_r[k])
        lower = np.append(lower, idx_r[k])
    upper = np.setdiff1d(indices, lower)
    return lower, upper


class _Parzen:
    """`NumericalParzenEstimator` (james rule) on [lb, ub] with quantisation q."""

    def __init__(self, samples, lb, ub, q):
        import numpy as np

        self.lb, self.ub, self.q = lb, ub, q
        mus = np.append(np.asarray(samples, dtype=float), 0.5 * (lb + ub))
        lo_sig, hi_sig = (ub - lb) / min(100.0, mus.size), ub - lb
        order = np.argsort(mus)
        smu = mus[order]
        prior_pos = int(np.where(np.arange(mus.size)[order] == mus.size - 1)[0][0])
        b = np.insert([smu[0], smu[-1]], 1, smu)
        sig = np.clip(np.maximum(b[1:-1] - b[0:-2], b[2:] - b[1:-1]), lo_sig, hi_sig)
        sig[prior_pos] = hi_sig
        self.mus, self.sigmas = mus, sig[np.argsort(order)]
        self.weights = np.ones(mus.size) / mus.size

    def _cdf(self, x, mu, s):
        import numpy as np
        from scipy.special import erf

        s = max(s, _EPS)
        norm = 1.0 / (0.5 * (1 + erf((self.ub - mu) / (1.41421356 * s))) - 0.5 * (1 + erf((self.lb - mu) / (1.41421356 * s))))
        return np.maximum(norm * 0.5 * (1.0 + erf((x - mu) / (1.41421356 * s))), _EPS)

    def loglik(self, xs):
        import numpy as np

        ps = np.zeros(xs.shape)
        for w, m, s in zip(self.weights, self.mus, self.sigmas):
            up = self._cdf(np.minimum(xs + 0.5 * self.q, self.ub), m, s)
            lo = self._cdf(np.maximum(xs + 0.5 * self.q, self.lb), m, s)  # as in the code (+0.5 q twice)
            ps += w * np.maximum(up - lo, _EPS)
        return np.log(ps + _EPS)

    def sample(self, npr, n):
        import numpy as np

        out = []
        while len(out) < n:
            k = int(np.argmax(npr.multinomial(1, self.weights)))
            while True:
                x = npr.normal(self.mus[k], max(self.sigmas[k], _EPS))
                if self.lb <= x <= self.ub:
                    break
            out.append(x)
        return np.round(np.asarray(out) / self.q) * self.q


class MOBOHB(_MFGenerator):
    """MO-BOHB as in the authors' code (`mobohb/hpbandster`): hpbandster Hyperband
    brackets (eta = 2, b_min = ceil(0.2 E), b_max = E -- MF-3 a), SH promotion by NDS
    keeping whole fronts (`SuccessiveHalvingMOBOHB`), configurations from the MOTPE
    generator: random with probability 1/6 or while no budget has more than
    2 n + 1 observations, otherwise per variable a Parzen-estimator TPE on the
    observations of the largest such budget (gamma = 0.10, 24 EI candidates). As in
    `search_space.as_uniform_space()`, every variable is an integer 0..k-1."""

    def __init__(self, space, budget, rng, *, max_epochs: int, gamma: float = 0.10, num_candidates: int = 24,
                 random_fraction: float = 1 / 6, num_initial_samples: int = 50):
        super().__init__(space, budget, rng, max_epochs=max_epochs, eta=2)
        import numpy as np

        from p3net.v005.common import initial_design_size

        self.gamma, self.n_cand, self.random_fraction = gamma, int(num_candidates), random_fraction
        # `get_MOBOHB(init=True)`: a first iteration of random configurations at the max
        # budget (MB2: num_initial_samples 50), sized by BB-4
        self.n_init = initial_design_size(num_initial_samples, int(budget))
        self.min_points = 2 * len(self.domains) + 1
        self.npr = np.random.RandomState(rng.randrange(2**31))
        b_min = math.ceil(0.2 * self.E)
        self.max_sh = -int(math.log(b_min / self.E) / math.log(self.eta)) + 1
        self.budgets = [self.E * self.eta ** (-k) for k in np.linspace(self.max_sh - 1, 0, self.max_sh)]
        self.history: list[tuple[Genotype, int, tuple[float, ...]]] = []

    def config(self) -> dict:
        return {**super().config(), "gamma": self.gamma, "num_candidates": self.n_cand,
                "random_fraction": self.random_fraction, "budgets": [max(1, round(b)) for b in self.budgets],
                "num_initial_samples": self.n_init}

    def _sample_tpe(self, obs) -> Genotype:
        import numpy as np

        gs = [g for g, _ in obs][::-1]  # `_load_hp_values` flips the history
        ys = np.array([f for _, f in obs][::-1], dtype=float)
        lower, upper = _motpe_split(ys, int(math.floor(self.gamma * len(ys))))
        values = []
        for i, k in enumerate(self.domains):
            if k < 2:
                values.append(0)
                continue
            x = np.array([g.values[i] / (k - 1) for g in gs])
            q = 1.0 / (k - 1)
            lb, ub = -0.5 * q, 1 + 0.5 * q
            pl, pu = _Parzen(x[lower], lb, ub, q), _Parzen(x[upper], lb, ub, q)
            cand = pl.sample(self.npr, self.n_cand)
            best = cand[int(np.argmax(pl.loglik(cand) - pu.loglik(cand)))]
            values.append(int(min(max(round((k - 1) * best), 0), k - 1)))
        return Genotype(values=tuple(values))

    def _get_config(self, budget: int) -> Genotype:
        from collections import Counter

        counts = Counter(b for _, b, _ in self.history)
        ok = [b for b, c in counts.items() if c > self.min_points]
        g = None
        if self.npr.rand() >= self.random_fraction and ok:
            top = max(ok)
            try:
                g = self._sample_tpe([(gg, f) for gg, b, f in self.history if b == top])
            except Exception:  # noqa: BLE001 -- the code falls back to a random configuration
                g = None
        if g is None or g in self.sampled:
            return self._new_config()
        self.sampled.add(g)
        return g

    def _run(self):
        import numpy as np

        if self.n_init > 0:  # `MOBOHB.get_next_iteration` with init_m: one stage at the max budget
            configs = [self._new_config() for _ in range(self.n_init)]  # generator in init mode: random
            objs = yield [(g, self.E) for g in configs]
            for g, f in zip(configs, objs):
                self.history.append((g, self.E, tuple(f)))
        it = 0
        while True:
            s = self.max_sh - 1 - (it % self.max_sh)
            n0 = int(math.floor(self.max_sh / (s + 1)) * self.eta**s)
            ns = [max(int(n0 * self.eta ** (-i)), 1) for i in range(s + 1)]
            budgets = [max(1, round(b)) for b in self.budgets[-s - 1:]]
            configs = [self._get_config(budgets[0]) for _ in range(ns[0])]
            for stage, b in enumerate(budgets):
                objs = yield [(g, b) for g in configs]
                for g, f in zip(configs, objs):
                    self.history.append((g, b, tuple(f)))
                if stage + 1 == len(budgets):
                    break
                rank = _nds_ranks(objs)
                keep, i = [], 0
                while len(keep) + int(np.sum(rank == i)) <= ns[stage + 1]:  # SuccessiveHalvingMOBOHB
                    keep.extend(np.flatnonzero(rank == i).tolist())
                    i += 1
                keep.extend(np.flatnonzero(rank == i).tolist())
                configs = [configs[j] for j in sorted(keep)]
            it += 1
