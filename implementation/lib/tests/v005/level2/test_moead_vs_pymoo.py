"""Level 2 (v005-level2-criteria.md): our MOEA/D vs pymoo 0.6.2 `MOEAD` with the same
categorical operators (uniform crossover, random-reset mutation p = 1/n), N = 20,
T = 4, Tchebycheff, prob_neighbor_mating 0.9. pymoo evaluates duplicate offspring, our
MOEA/D re-draws them (#20, #35), so pymoo's run is read up to its first BUDGET distinct
evaluations. Criterion (fixed before the test):
median HV over 100 seeds within +-2 % of pymoo's, and a TOST equivalence test with
margin +-2 % of pymoo's median at alpha = 0.05.

Run in implementation/experiments/.venv (pymoo).
"""

from __future__ import annotations

import random

import numpy as np
import pytest
from scipy import stats

pymoo = pytest.importorskip("pymoo")

DOMAINS = [8] * 10
BUDGET = 400
SEEDS = range(100)  # protocol decision 2 (changed 2026-10-19): 100 runs; 20-30 had no power for HV spread ~3 %


def _objective():
    rng = random.Random(0)
    w1 = [[rng.random() for _ in range(k)] for k in DOMAINS]
    w2 = [[1.0 - x + 0.3 * rng.random() for x in row] for row in w1]

    def f(x):
        x = [int(v) for v in x]
        a = sum(w1[i][v] for i, v in enumerate(x))
        b = sum(w2[i][v] for i, v in enumerate(x))
        return a, b

    return f


def _hv(points, ref=(11.0, 14.0)):
    pts = sorted(p for p in points if p[0] < ref[0] and p[1] < ref[1])
    hv, best = 0.0, ref[1]
    for x, y in pts:
        if y < best:
            hv += (ref[0] - x) * (best - y)
            best = y
    return hv


def _ours(seed):
    from p3net.harness.runner import Observation, RunState
    from p3net.problem.genotype import CategoricalDomain, SearchSpace
    from p3net.v005.baselines.library import MOEAD

    f = _objective()
    space = SearchSpace(domains=tuple(CategoricalDomain(values=tuple(range(k))) for k in DOMAINS))
    m = MOEAD(space, BUDGET, random.Random(seed))
    state, pts = RunState(), []
    while state.evaluations_used < BUDGET:
        props = m.propose(state)
        if not props:
            break
        new = [Observation(genotype=g, objectives=f(g.values)) for g in props]
        pts.extend(o.objectives for o in new)
        state.evaluations_used += len(new)
        m.update(state, new)
    return _hv(pts)


def _pymoo(seed):
    from pymoo.algorithms.moo.moead import MOEAD
    from pymoo.core.mutation import Mutation
    from pymoo.core.problem import Problem
    from pymoo.operators.crossover.ux import UniformCrossover
    from pymoo.operators.sampling.rnd import IntegerRandomSampling
    from pymoo.optimize import minimize
    from pymoo.util.ref_dirs import get_reference_directions

    f = _objective()
    seen: list[tuple[float, float]] = []

    class P(Problem):
        def __init__(self):
            super().__init__(n_var=len(DOMAINS), n_obj=2, xl=0, xu=np.array(DOMAINS) - 1, vtype=int)

        def _evaluate(self, X, out, *args, **kwargs):
            F = np.array([f(np.round(x)) for x in X])
            seen.extend(tuple(r) for r in F)  # objective vectors identify genotypes here (continuous weights)
            out["F"] = F

    class RandomReset(Mutation):
        def _do(self, problem, X, **kwargs):
            X = np.round(X).astype(int)
            mask = np.random.random(X.shape) < 1.0 / problem.n_var
            X[mask] = np.random.randint(0, np.array(DOMAINS)[np.where(mask)[1]])
            return X

    algo = MOEAD(get_reference_directions("uniform", 2, n_partitions=19), n_neighbors=4,
                 prob_neighbor_mating=0.9, sampling=IntegerRandomSampling(),
                 crossover=UniformCrossover(), mutation=RandomReset())
    # pymoo evaluates duplicates (~19 % of its evaluations here); with #20/#35 they cost no
    # budget, so the reference is pymoo's first BUDGET *distinct* evaluated points
    minimize(P(), algo, ("n_eval", 4 * BUDGET), seed=seed, verbose=False, save_history=False)
    distinct = list(dict.fromkeys(seen))[:BUDGET]
    return _hv(distinct)


def test_level2_moead_hv_equivalent_to_pymoo():
    ours = np.array([_ours(s) for s in SEEDS])
    ref = np.array([_pymoo(s) for s in SEEDS])
    med_ref = float(np.median(ref))
    margin = 0.02 * med_ref
    assert abs(float(np.median(ours)) - med_ref) <= margin, (np.median(ours), med_ref)
    # TOST (Welch): H0 |mean(ours) - mean(ref)| >= margin
    p_low = stats.ttest_ind(ours + margin, ref, equal_var=False, alternative="greater").pvalue
    p_high = stats.ttest_ind(ours - margin, ref, equal_var=False, alternative="less").pvalue
    assert max(p_low, p_high) < 0.05, (p_low, p_high, ours.mean(), ref.mean())
