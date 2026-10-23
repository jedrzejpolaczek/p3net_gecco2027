"""NSGANetV2 / MSuNAS as in the authors' code (card `nsganetv2.md`; github.com/
mikelzc1990/nsganetv2 `msunas.py`, `acc_predictor/*`).

Loop: N = min(100, floor(0.25 b)) random architectures (O-V3), then iterations of
K = 8 real evaluations: fit Adaptive Switching predictors (V-1 a: pool {RBF, GP,
CART}, CV folds min(10, floor(N/3)) -- Z-V1 -- winner = argmax mean(tau) - std(tau)),
one for f1 and one for f2 (O-V1: f2 is predicted, #6); run the inner NSGA-II on the
predicted objectives (pop 40, 20 generations, start from the archive's
non-dominated set, integer two-point crossover p = 0.9, integer polynomial
mutation eta = 1, duplicate elimination); drop candidates already in the archive;
choose K by the subset GA minimising the spread of gaps on the f2 axis (V-2 a).
No supernet / fine-tuning (O-V2).

Predictors: RBF = cubic kernel with a linear tail (scipy RBFInterpolator, equivalent of
pySOT's RBFInterpolant(CubicKernel, LinearTail) -- identical rankings at level 2); GP =
the authors' pydacefit DACE (linear regression, Gaussian correlation); CART = the
authors' ensemble of 5000 trees on random feature subsets.
"""

from __future__ import annotations

import math

import numpy as np
from scipy.interpolate import RBFInterpolator
from scipy.stats import kendalltau
from sklearn.tree import DecisionTreeRegressor

from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import dominates, fast_nondominated_sort
from p3net.v005.baselines.nsga_net import binary_tournament, int_polynomial_mutation, rank_and_crowding
from p3net.v005.common import EvalCache, cardinalities, initial_design_size, is_valid, random_genotype

N_DOE, K_ITER = 100, 8
INNER_POP, INNER_GENS = 40, 20
SUBSET_POP, SUBSET_GENS = 100, 60
CART_TREES = 5000  # acc_predictor/factory.py: CART(n_tree=5000)


class _RBF:
    name = "rbf"

    def fit(self, X, y, rng):
        self.m = RBFInterpolator(X, y, kernel="cubic", degree=1)
        return self

    def predict(self, X):
        return self.m(np.asarray(X, float))


class _GP:
    """`acc_predictor/gp.py`: pydacefit DACE, linear regression, Gaussian correlation,
    theta = 1 in [1e-5, 100] (level-2 decision 2026-10-21: the authors' library)."""

    name = "gp"

    def fit(self, X, y, rng):
        from pydacefit.corr import corr_gauss
        from pydacefit.dace import DACE, regr_linear

        # theta as a one-element array: the same isotropic model as the scalar 1.0 of gp.py
        # (pydacefit 1.0.1 calls np.where on it, which numpy >= 2 refuses for 0-d arrays)
        self.m = DACE(regr=regr_linear, corr=corr_gauss, theta=np.array([1.0]), thetaL=np.array([0.00001]),
                      thetaU=np.array([100.0]))
        self.m.fit(np.asarray(X, float), np.asarray(y, float))
        return self

    def predict(self, X):
        return np.ravel(self.m.predict(np.asarray(X, float)))


class _CART:
    name = "cart"

    def __init__(self, n_tree: int = CART_TREES):
        self.n_tree = n_tree

    def fit(self, X, y, rng):
        npr = np.random.default_rng(rng.getrandbits(64))
        self.trees = []
        for _ in range(self.n_tree):
            idx = npr.permutation(len(X))
            feats = npr.permutation(X.shape[1])[: npr.integers(1, X.shape[1] + 1)]
            t = DecisionTreeRegressor(random_state=int(npr.integers(2**31)))
            t.fit(X[idx][:, feats], y[idx])
            self.trees.append((t, feats))
        return self

    def predict(self, X):
        X = np.asarray(X, float)
        return np.mean([t.predict(X[:, f]) for t, f in self.trees], axis=0)


_POOL = {"rbf": _RBF, "gp": _GP, "cart": _CART}


def adaptive_switching(X, y, rng, return_scores: bool = False):
    """V-1 a + Z-V1: pick the predictor maximising mean - std of Kendall's tau over
    min(10, floor(N/3)) folds, refit it on all data."""
    X, y = np.asarray(X, float), np.asarray(y, float)
    n = len(y)
    n_folds = max(2, min(10, n // 3))
    perm = list(range(n))
    rng.shuffle(perm)
    folds = [perm[k::n_folds] for k in range(n_folds)]
    scores: dict[str, list[float]] = {k: [] for k in _POOL}
    failed: set[str] = set()
    for tst in folds:
        trn = sorted(set(range(n)) - set(tst))
        for name, cls in _POOL.items():
            try:
                pred = cls().fit(X[trn], y[trn], rng).predict(X[tst])
                tau = kendalltau(pred, y[tst]).statistic
            except Exception:  # noqa: BLE001 -- e.g. RBF/GP with fewer points than d + 1
                failed.add(name)
                tau = math.nan
            scores[name].append(0.0 if tau is None or math.isnan(tau) else float(tau))
    # Z-V2 (2026-10-23): a model that could not be fitted on some fold (too few points for
    # its dimension -- the authors' code asserts N > d instead) is not eligible; the winner
    # is refit on all data, falling back to the next eligible model if that fails too.
    crit = {k: (float(np.mean(v)) - float(np.std(v))) if k not in failed else -math.inf for k, v in scores.items()}
    for winner in sorted(crit, key=crit.get, reverse=True):
        try:
            model = _POOL[winner]().fit(X, y, rng)
            break
        except Exception:  # noqa: BLE001
            continue
    return (winner, model, scores) if return_scores else (winner, model)


def _int_two_point(p1: Genotype, p2: Genotype, rng, prob: float = 0.9):
    if rng.random() >= prob or len(p1.values) < 3:
        return p1, p2
    from p3net.v005.baselines.nsga_net import two_point_crossover

    return two_point_crossover(p1, p2, rng)


def inner_nsga2(archive: list[Observation], predictor, domains, rng) -> list[Genotype]:
    """W-V3: NSGA-II on (f1_hat, f2_hat), seeded with the archive's non-dominated
    genotypes; returns the final population (code: `res.pop`)."""
    nd = fast_nondominated_sort(archive, lambda o: tuple(o.objectives))[0]
    start = list(dict.fromkeys(o.genotype for o in nd))[:INNER_POP]
    F = np.asarray(predictor(start), float)
    pop = [Observation(genotype=g, objectives=tuple(F[i])) for i, g in enumerate(start)]
    pop, info = rank_and_crowding(pop, INNER_POP, rng)
    for _ in range(INNER_GENS):
        kids: list[Genotype] = []
        seen = {o.genotype for o in pop}
        for _ in range(100):
            if len(kids) >= INNER_POP:
                break
            def pick():
                i, j = rng.randrange(len(pop)), rng.randrange(len(pop))
                a, b = (pop[i].objectives, info[i][1]), (pop[j].objectives, info[j][1])
                return pop[i] if binary_tournament(a, b, rng) == 0 else pop[j]
            c1, c2 = _int_two_point(pick().genotype, pick().genotype, rng)
            for c in (c1, c2):
                c = int_polynomial_mutation(c, domains, rng, eta=1.0)
                if c not in seen and len(kids) < INNER_POP:
                    seen.add(c)
                    kids.append(c)
        if not kids:
            break
        Fk = np.asarray(predictor(kids), float)
        pop, info = rank_and_crowding(pop + [Observation(genotype=g, objectives=tuple(Fk[i]))
                                             for i, g in enumerate(kids)], INNER_POP, rng)
    return [o.genotype for o in pop]


def subset_selection(cand_f2, nd_f2, K: int, rng):
    """V-2 a (`SubsetProblem`): a boolean GA (pop 100, 60 generations; sampling,
    crossover and mutation keep exactly K selected) minimising
    std(diff(sort(nd_f2 + chosen_f2))). Returns a boolean mask."""
    cand_f2, nd_f2 = np.asarray(cand_f2, float), np.asarray(nd_f2, float)
    n = len(cand_f2)
    if n <= K:
        return np.ones(n, dtype=bool)

    def f(mask):
        return float(np.std(np.diff(np.sort(np.concatenate([nd_f2, cand_f2[mask]])))))

    def sample():
        m = np.zeros(n, dtype=bool)
        m[rng.sample(range(n), K)] = True
        return m

    pop = [sample() for _ in range(SUBSET_POP)]
    fit = [f(m) for m in pop]
    for _ in range(SUBSET_GENS):
        kids = []
        for _ in range(SUBSET_POP):
            i, j = rng.randrange(SUBSET_POP), rng.randrange(SUBSET_POP)
            p1 = pop[i] if fit[i] <= fit[j] else pop[j]
            i, j = rng.randrange(SUBSET_POP), rng.randrange(SUBSET_POP)
            p2 = pop[i] if fit[i] <= fit[j] else pop[j]
            child = p1 & p2  # BinaryCrossover: common ones, the rest from the xor
            xor = list(np.flatnonzero(p1 ^ p2))
            rng.shuffle(xor)
            child = child.copy()
            child[xor[: K - int(child.sum())]] = True
            on, off = list(np.flatnonzero(child)), list(np.flatnonzero(~child))  # MyMutation: one swap
            if on and off:
                child[rng.choice(off)], child[rng.choice(on)] = True, False
            kids.append(child)
        allp = pop + kids
        allf = fit + [f(m) for m in kids]
        uniq, order = {}, sorted(range(len(allp)), key=lambda k: allf[k])
        for k in order:
            key = allp[k].tobytes()
            if key not in uniq:
                uniq[key] = k
            if len(uniq) >= SUBSET_POP:
                break
        pop, fit = [allp[k] for k in uniq.values()], [allf[k] for k in uniq.values()]
        while len(pop) < SUBSET_POP:
            m = sample()
            pop.append(m)
            fit.append(f(m))
    return pop[int(np.argmin(fit))]


class NSGANetV2:
    def __init__(self, space, budget, rng):
        self.space, self.rng, self.budget = space, rng, int(budget)
        self.domains = cardinalities(space)
        self.n_doe = initial_design_size(N_DOE, self.budget)
        self.cache = EvalCache()
        self.used = 0
        self._pending: list[Genotype] = []
        self.winners: list[tuple[str, str]] = []

    def config(self) -> dict:
        return {"n_doe": self.n_doe, "n_iter": K_ITER, "pool": sorted(_POOL), "inner_pop": INNER_POP,
                "inner_gens": INNER_GENS, "cart_trees": CART_TREES}

    def _x(self, gs):
        return np.array([g.values for g in gs], dtype=float)

    def _next(self, k: int) -> list[Genotype]:
        hist = self.cache.history()
        X = self._x([o.genotype for o in hist])
        Y = np.array([o.objectives for o in hist], dtype=float)
        n1, m1 = adaptive_switching(X, Y[:, 0], self.rng)
        n2, m2 = adaptive_switching(X, Y[:, 1], self.rng)
        self.winners.append((n1, n2))

        def predictor(gs):
            Xg = self._x(gs)
            return np.column_stack([np.ravel(m1.predict(Xg)), np.ravel(m2.predict(Xg))])

        cands = [g for g in inner_nsga2(hist, predictor, self.domains, self.rng)
                 if g not in self.cache and is_valid(self.space, g)]
        cands = list(dict.fromkeys(cands))
        while len(cands) < k:  # too few new candidates: fill at random (not in the code)
            g = random_genotype(self.space, self.rng)
            if g not in self.cache and g not in cands:
                cands.append(g)
        if len(cands) == k:
            return cands
        nd = fast_nondominated_sort(hist, lambda o: tuple(o.objectives))[0]
        mask = subset_selection(predictor(cands)[:, 1], [o.objectives[1] for o in nd], k, self.rng)
        return [g for g, keep in zip(cands, mask) if keep]

    def propose(self, state: RunState) -> list[Genotype]:
        remaining = self.budget - self.used
        if remaining <= 0 or self._pending:
            return []
        if len(self.cache) == 0:
            batch: list[Genotype] = []
            while len(batch) < min(self.n_doe, remaining):
                g = random_genotype(self.space, self.rng)
                if g not in batch:
                    batch.append(g)
        else:
            batch = self._next(min(K_ITER, remaining))
        self._pending = batch
        self.used += len(batch)
        return list(batch)

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(obs.genotype, obs.objectives)
        self._pending = []
