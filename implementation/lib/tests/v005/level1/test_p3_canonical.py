"""Level-1 tests for canonical P3 without a surrogate (card
`notes/plans/v005-sources/p3-canonical.md`, W-K1-W-K5; W1-W16 are shared
with `test_p3net.py`, parametrised over both engines there).

Source: Goldman & Punch, GECCO'14 (P22, P25 literally: every changing mixing
step is one real evaluation). Decisions K-1 a (same engine as P3Net with an
exchangeable step evaluator), K-2 a (stop immediately at the b-th real
evaluation).
"""

from __future__ import annotations

import random

import pytest

from ._support import (
    CountingObjective,
    EventLog,
    G,
    additive_cost,
    assert_budget_respected,
    drive,
    make,
    random_weights,
    trap_f1,
    trap_space,
    vals,
)


def _obj(log=None, f2=None):
    f1 = trap_f1(3, 9)
    return CountingObjective(f1, f2 or additive_cost(random_weights([3] * 9, seed=7)), log=log)


def test_WK1_no_surrogate_object_and_no_surrogate_calls(monkeypatch):
    """W-K1: canonical P3 never creates a surrogate object and never calls
    one (every step is a real evaluation)."""
    from p3net.v005.methods import P3Canonical
    from p3net.v005.surrogates import pairwise

    touched = []
    for name in ("__init__", "fit", "features", "predict_delta", "predict_chain"):
        orig = getattr(pairwise.PairwiseSurrogate, name)

        def spy(self, *a, _n=name, _o=orig, **k):
            touched.append(_n)
            return _o(self, *a, **k)

        monkeypatch.setattr(pairwise.PairwiseSurrogate, name, spy)
    obj = _obj()
    drive(make(P3Canonical, trap_space(3, 3, 3), 400, 0), obj, 400)
    assert touched == [], f"surrogate used by canonical P3: {sorted(set(touched))}"
    assert obj.n > 0


def test_WK2_each_changing_mixing_step_costs_one_real_evaluation():
    """W-K2 (P22, P25): every mixing step that changes the solution consumes
    exactly one real evaluation of that candidate, unless the candidate is
    already in H_t (then zero, W15); a step that does not change it costs
    nothing."""
    from p3net.v005.methods import P3Canonical

    log = EventLog()
    obj = _obj(log)
    drive(make(P3Canonical, trap_space(3, 3, 3), 1200, 0, observer=log), obj, 1200)
    seen: set[tuple] = set()
    steps = 0
    evals_since_event = 0
    events = list(log)
    for i, (k, p) in enumerate(events):
        if k == "eval":
            assert p["genotype"] not in seen, "a genotype from H_t was evaluated again"
            seen.add(p["genotype"])
            evals_since_event += 1
            continue
        if k == "cluster_step":
            steps += 1
            assert evals_since_event <= 1, "more than one real evaluation for one mixing step"
            cand = vals(p["candidate"])
            evaluated_here = (
                i > 0 and events[i - 1][0] == "eval" and events[i - 1][1]["genotype"] == cand
            )
            if not p["changed"]:
                assert not evaluated_here, "an unchanged solution was evaluated"
            elif not evaluated_here:
                assert cand in seen, "a changed candidate was neither evaluated nor taken from H_t"
        evals_since_event = 0
    assert steps > 0


def test_WK3_oracle_surrogate_reproduces_canonical_trajectory():
    """W-K3 (K-1 a): on the same seed, P3Net with an oracle surrogate
    (prediction = true value, every call counted as an evaluation) yields
    exactly the same sequence of evaluated genotypes as canonical P3 -- the
    surrogate is the only difference between the two methods."""
    from p3net.v005.methods import P3Canonical, P3Net

    space = trap_space(3, 3, 3)
    for seed in range(3):
        a, b = _obj(), _obj()
        drive(make(P3Canonical, space, 500, seed), a, 500)
        drive(make(P3Net, space, 500, seed, step_evaluator="oracle"), b, 500)
        assert a.calls == b.calls, f"seed {seed}: trajectories diverge at step " + str(
            next(
                (i for i, (x, y) in enumerate(zip(a.calls, b.calls)) if x != y),
                min(len(a.calls), len(b.calls)),
            )
        )


@pytest.mark.parametrize("budget", [1, 7, 19, 137, 500])
def test_WK4_budget_never_exceeded_and_stops_mid_iteration(budget):
    """W-K4 (K-2 a): the run ends after exactly b real evaluations (budgets
    chosen to end inside FIHC, n=9 -> 18 per pass, and inside mixing)."""
    from p3net.v005.methods import P3Canonical

    obj = _obj()
    drive(make(P3Canonical, trap_space(3, 3, 3), budget, 1), obj, budget)
    assert_budget_respected(obj, budget, exact=True)


def test_WK4_budget_object_rule():
    """W-K4 (K-2 a, #35): Budget.charge returns False once b distinct
    evaluations were charged; genotypes already in the cache never consume
    budget."""
    from p3net.v005.common import Budget, EvalCache

    b, c = Budget(3), EvalCache()
    c.put(G(9, 9), (1.0, 1.0))
    for _ in range(5):
        b.charge(G(9, 9), c)  # cached: free
    for i in range(3):
        assert b.charge(G(i, 0), c) is True
        c.put(G(i, 0), (float(i), 0.0))
    assert b.charge(G(5, 5), c) is False


def test_WK5_single_objective_mode_is_well_defined():
    """W-K5 (precondition of the level-2 comparison with the authors' code,
    which is not a level-1 test): with a constant second objective, canonical
    P3 is single-objective P3 -- its trajectory is identical to the one with
    f2 = f1 (both reduce D-1 to 'f1 strictly better / not worse')."""
    from p3net.v005.methods import P3Canonical

    f1 = trap_f1(3, 9)
    space = trap_space(3, 3, 3)
    for seed in range(3):
        const = CountingObjective(f1, lambda g: 1.0)
        same = CountingObjective(f1, f1)
        drive(make(P3Canonical, space, 800, seed), const, 800)
        drive(make(P3Canonical, space, 800, seed), same, 800)
        assert const.calls == same.calls


def test_WK_guard_random_sanity():
    """Helper guard: different seeds give different canonical-P3 runs (so the
    W-K3 equality is not trivially due to a seed-independent method)."""
    from p3net.v005.methods import P3Canonical

    a, b = _obj(), _obj()
    drive(make(P3Canonical, trap_space(3, 3, 3), 60, 0), a, 60)
    drive(make(P3Canonical, trap_space(3, 3, 3), 60, 1), b, 60)
    assert a.calls != b.calls
    assert random.Random(0).random() != random.Random(1).random()
