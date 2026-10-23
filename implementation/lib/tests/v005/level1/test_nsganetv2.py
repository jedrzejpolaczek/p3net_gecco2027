"""Level-1 tests for NSGANetV2 / MSuNAS (card
`notes/plans/v005-sources/nsganetv2.md`, W-V1-W-V6).

Source: Lu et al., NSGANetV2, ECCV 2020, Alg. 1, §3.3, §4.1, §4.3; authors'
code github.com/mikelzc1990/nsganetv2 (`msunas.py`: `_subset_selection`,
`SubsetProblem`; `acc_predictor/adaptive_switching.py`). Card decisions:
V-1 a + Z-V1 (AS over {RBF, GP, CART}, folds min(10, floor(N/3))), V-2 a
(subset selection as in the code), O-V1 (f2 predicted by a second AS).
"""

from __future__ import annotations

import itertools
import random

import numpy as np
import pytest

from p3net.harness.runner import Observation
from p3net.problem.objectives import dominates

from ._support import (
    CountingObjective,
    G,
    additive_cost,
    assert_budget_respected,
    assert_no_benchmark_access,
    drive,
    drive_batches,
    make,
    random_weights,
    space_of,
    vals,
)


def _m():
    from p3net.v005.baselines import nsganetv2

    return nsganetv2


def _conflicting(domains, seed=0):
    w1 = random_weights(domains, seed)
    w2 = [[1.0 - x for x in row] for row in w1]
    return CountingObjective(additive_cost(w1), additive_cost(w2))


@pytest.mark.parametrize("budget,start", [(50, 12), (100, 25)])
def test_WV1_start_then_iterations_of_eight(budget, start):
    """W-V1 (O-V3, K-2): N = min(100, floor(0.25 b)) random, really
    evaluated architectures first; then iterations of K = 8 evaluations, the
    last one possibly shorter; exactly b evaluations."""
    obj = _conflicting([4] * 6)
    batches = drive_batches(make(_m().NSGANetV2, space_of([4] * 6), budget, 0), obj, budget)
    assert len(batches[0]) == start and len(set(batches[0])) == start
    assert all(len(b) == 8 for b in batches[1:-1])
    assert 1 <= len(batches[-1]) <= 8
    assert_budget_respected(obj, budget, exact=True)


def test_WV2_adaptive_switching_pool():
    """W-V2 (V-1 a): AS chooses among {RBF, GP, CART} only (no MLP) and
    returns a fitted model."""
    rng = np.random.default_rng(0)
    X = rng.integers(0, 4, size=(30, 6)).astype(float)
    y = X @ np.array([0.5, -1.0, 0.2, 0.0, 0.3, 1.0]) + 0.01 * rng.standard_normal(30)
    name, model = _m().adaptive_switching(X, y, random.Random(0))
    assert str(name).lower() in {"rbf", "gp", "cart"}
    pred = np.asarray(model.predict(X)).ravel()
    assert pred.shape == (30,)


@pytest.mark.parametrize("n,folds", [(12, 4), (30, 10), (60, 10), (15, 5)])
def test_WV2_selection_criterion_and_fold_count(n, folds):
    """W-V2 (V-1 a, Z-V1): the winner maximises mean(tau) - std(tau) over CV
    folds; the number of folds is min(10, floor(N/3)). Every training fold
    has >= d + 1 = 7 points, so all three models qualify (Z-V2)."""
    rng = np.random.default_rng(1)
    X = rng.integers(0, 4, size=(n, 6)).astype(float)
    y = np.sin(X[:, 0]) + X[:, 1] * X[:, 2]
    name, _, scores = _m().adaptive_switching(X, y, random.Random(0), return_scores=True)
    assert set(scores) == {"rbf", "gp", "cart"}
    crit = {k: float(np.mean(v)) - float(np.std(v)) for k, v in scores.items()}
    assert name == max(crit, key=crit.get)
    assert all(len(v) == folds for v in scores.values())


@pytest.mark.parametrize("n", [3, 6, 10])
def test_WV2_too_few_points_cart_wins(n):
    """W-V2 (Z-V2 of 2026-10-23): a model that cannot be fitted in some fold
    (RBF with linear tail and GP need >= d + 1 points) is not a candidate --
    with N <= d (d = 10) the winner is CART, and AS does not raise."""
    rng = np.random.default_rng(n)
    X = rng.integers(0, 4, size=(n, 10)).astype(float)
    y = X[:, 0] - 0.5 * X[:, 1] + 0.1 * np.arange(n)
    name, model = _m().adaptive_switching(X, y, random.Random(0))
    assert str(name).lower() == "cart"
    assert np.asarray(model.predict(X)).ravel().shape == (n,)


def test_WV2_small_initial_design_propose_does_not_raise():
    """W-V2 / W-V1 (Z-V2): with b = 20 on a 10-variable space the initial
    design is min(100, 5) = 5 <= d points; the run proceeds (AS falls back to
    CART) and spends exactly b evaluations."""
    obj = _conflicting([3] * 10)
    drive(make(_m().NSGANetV2, space_of([3] * 10), 20, 0), obj, 20)
    assert_budget_respected(obj, 20, exact=True)


def test_WV3_inner_nsga2_on_predicted_objectives():
    """W-V3 (code: pop 40, 20 generations, start from the archive's
    non-dominated set, two-point crossover p = 0.9, integer polynomial
    mutation eta = 1, deduplication; objectives = (f1_hat, f2_hat)): the
    result is non-dominated under the predictor, in range, distinct, and the
    predictor is queried at most 40 x 21 times."""
    domains = [4] * 6
    w1 = random_weights(domains, 0)
    f1 = additive_cost(w1)
    f2 = additive_cost([[1.0 - x for x in row] for row in w1])
    rng = random.Random(0)
    archive = [
        Observation(genotype=G(*(rng.randrange(4) for _ in range(6))), objectives=(0.0, 0.0))
        for _ in range(15)
    ]
    archive = [
        Observation(genotype=o.genotype, objectives=(f1(o.genotype), f2(o.genotype)))
        for o in archive
    ]
    calls = []

    def predictor(genotypes):
        calls.extend(vals(g) for g in genotypes)
        return np.array([[f1(g), f2(g)] for g in genotypes])

    out = [vals(g) for g in _m().inner_nsga2(archive, predictor, domains, random.Random(1))]
    assert len(out) == len(set(out)) > 0
    assert all(0 <= v < 4 for g in out for v in g)
    preds = {g: (f1(g), f2(g)) for g in out}
    for a, b in itertools.permutations(out, 2):
        assert not dominates(preds[a], preds[b]), "inner NSGA-II returned a dominated candidate"
    assert len(calls) <= 40 * 21


def test_WV4_candidates_in_archive_rejected():
    """W-V4 (code): candidates already in the archive are rejected before
    subset selection -- on a 64-genotype space no genotype is evaluated
    twice."""
    obj = _conflicting([2] * 6)
    drive(make(_m().NSGANetV2, space_of([2] * 6), 40, 0), obj, 40)
    assert len(set(obj.calls)) == len(obj.calls)


def _gap_std(archive_f2, chosen_f2):
    tmp = np.sort(np.concatenate([np.asarray(archive_f2, float), np.asarray(chosen_f2, float)]))
    return float(np.std(np.diff(tmp)))


def _as_indices(sel, n):
    arr = np.asarray(sel)
    if arr.dtype == bool and arr.size == n:
        return sorted(np.flatnonzero(arr).tolist())
    return sorted(int(i) for i in arr.ravel())


def test_WV5_subset_selection_picks_K_minimising_gap_spread():
    """W-V5 (code `_subset_selection` / `SubsetProblem`): exactly K
    candidates; the GA (pop 100, 60 gens) minimises std(diff(sort(archive_f2
    + chosen_f2))) -- on a small instance it reaches the brute-force optimum
    (within 5 %)."""
    rng = np.random.default_rng(3)
    cand = rng.uniform(0, 10, size=10)
    nd = np.array([0.0, 10.0, 4.0])
    for K in (2, 3, 4):
        sel = _as_indices(_m().subset_selection(cand, nd, K, random.Random(0)), len(cand))
        assert len(sel) == K == len(set(sel))
        best = min(_gap_std(nd, cand[list(c)]) for c in itertools.combinations(range(len(cand)), K))
        assert _gap_std(nd, cand[sel]) <= best * 1.05 + 1e-12


def test_WV6_no_f2_access_and_budget():
    """W-V6 (#6, O-V1, K-2): no benchmark/f2 hook; budget never exceeded."""
    assert_no_benchmark_access(_m().NSGANetV2)
    obj = _conflicting([3] * 6)
    drive(make(_m().NSGANetV2, space_of([3] * 6), 37, 5), obj, 37)
    assert_budget_respected(obj, 37, exact=True)
