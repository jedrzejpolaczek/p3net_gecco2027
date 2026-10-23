"""Level-1 tests for MO-DSA-P3-GOMEA and MO-PSA-P3-GOMEA (card
`notes/plans/v005-sources/bartnik-mo-sa-p3-gomea.md`, W-B1-W-B13).

Sources: N. Bartnik, MSc thesis 2026, §4.5.4 (Alg. 7-8), §5.2-5.4, §6.3-6.4
(Alg. 9, Eq. 6.1-6.4); Dushatskiy et al., GECCO'21 (SA-P3-GOMEA). Card
decisions: B-1 a (RF per objective), B-2 a (warm-up 20 % of the budget),
B-3 a (gamma = 0.999), assumptions Z-B0-Z-B4.
"""

from __future__ import annotations

import math
import random

import pytest
from scipy.stats import norm

from p3net.problem.objectives import dominates, pareto_front

from ._support import (
    CountingObjective,
    EventLog,
    additive_cost,
    assert_budget_respected,
    assert_no_benchmark_access,
    drive,
    make,
    random_weights,
    space_of,
    trap_f1,
    trap_space,
    vals,
)

METHODS = ["MODSA", "MOPSA"]


def _cls(name):
    from p3net.v005 import bartnik

    return getattr(bartnik, name)


def _run(name, budget=60, seed=0, space=None, f1=None, f2=None):
    space = space or trap_space(3, 3, 3)
    n = len(space.domains)
    log = EventLog()
    obj = CountingObjective(
        f1 or trap_f1(3, n), f2 or additive_cost(random_weights([3] * n, seed=2)), log=log
    )
    m = make(_cls(name), space, budget, seed, observer=log)
    drive(m, obj, budget)
    return m, obj, log


# ---------------------------------------------------------------------------
# Pure functions: Eq. 6.1, quantile, alpha schedule, PSA acceptance
# ---------------------------------------------------------------------------


def test_WB8_dominance_probability_hand_values():
    """W-B8 (B13, Eq. 6.1, in our minimisation convention for both
    objectives): P(new > old) = Phi((m1_old - m1_new)/sqrt(s1n^2+s1o^2)) *
    Phi((m2_old - m2_new)/sqrt(s2n^2+s2o^2))."""
    from p3net.v005.bartnik import dominance_probability

    p = dominance_probability((0.0, 2.0), (1.0, 1.0), (1.0, 3.0), (1.0, 1.0))
    expected = norm.cdf(1 / math.sqrt(2)) ** 2
    assert math.isclose(p, expected, rel_tol=1e-9)
    p2 = dominance_probability((1.0, 1.0), (0.5, 2.0), (1.5, 0.0), (0.0, 1.0))
    expected2 = norm.cdf(0.5 / 0.5) * norm.cdf(-1.0 / math.sqrt(5.0))
    assert math.isclose(p2, expected2, rel_tol=1e-9)


def test_WB8_dominance_probability_zero_sigma_is_a_step():
    """W-B8 (B13: archive members have sigma = 0; the factor is a 0/1 step)."""
    from p3net.v005.bartnik import dominance_probability

    z = (0.0, 0.0)
    assert dominance_probability((1.0, 1.0), z, (2.0, 2.0), z) == 1.0
    assert dominance_probability((1.0, 3.0), z, (2.0, 2.0), z) == 0.0
    assert dominance_probability((3.0, 1.0), z, (2.0, 2.0), z) == 0.0
    half = dominance_probability((1.0, 1.0), (0.0, 1.0), (2.0, 1.0), (0.0, 0.0))  # step x Phi(0)
    assert math.isclose(half, 0.5)


def test_WB10_quantile_threshold_is_alpha_quantile():
    """W-B10 (B14): the threshold is the alpha-quantile of the history (values
    chosen at order statistics so every quantile definition agrees)."""
    from p3net.v005.bartnik import quantile_threshold

    h = [4.0, 0.0, 3.0, 1.0, 2.0]
    assert quantile_threshold(h, 0.5) == 2.0
    assert quantile_threshold(h, 0.25) == 1.0
    assert quantile_threshold(h, 1.0) == 4.0
    assert quantile_threshold(h, 0.0) == 0.0


def test_WB10_quantile_threshold_is_numpy_linear():
    """W-B10 (B14; interfaces §7 Q-12): threshold =
    numpy.quantile(history, alpha, method="linear"), also between order
    statistics."""
    import numpy as np

    from p3net.v005.bartnik import quantile_threshold

    rng = random.Random(4)
    for _ in range(50):
        h = [rng.uniform(-3, 3) for _ in range(rng.randrange(2, 40))]
        a = rng.random()
        assert math.isclose(
            quantile_threshold(h, a),
            float(np.quantile(h, a, method="linear")),
            rel_tol=1e-12,
            abs_tol=1e-12,
        )


def test_WB7_alpha_starts_at_one_decays_and_resets():
    """W-B7 (B5, B2): alpha = 1 at start; x gamma after an iteration with an
    unchanged archive; reset to 1 when the archive changed."""
    from p3net.v005.bartnik import AlphaSchedule

    s = AlphaSchedule()
    assert math.isclose(s.end_iteration(False), 0.999)
    assert math.isclose(s.end_iteration(False), 0.999**2)
    assert s.end_iteration(True) == 1.0
    assert math.isclose(s.end_iteration(False), 0.999)
    s9 = AlphaSchedule(gamma=0.9)
    for i in range(1, 6):
        assert math.isclose(s9.end_iteration(False), 0.9**i)


def test_WB7_first_iteration_with_change_keeps_alpha_one():
    """W-B7: alpha starts at 1 (so a first iteration that changes the
    archive leaves it at exactly 1)."""
    from p3net.v005.bartnik import AlphaSchedule

    assert AlphaSchedule().end_iteration(True) == 1.0


@pytest.mark.parametrize(
    "p_keep,p_revert,tau,keep",
    [
        (0.2, 0.7, 0.5, False),  # p_revert >= tau and > p_keep -> revert
        (0.2, 0.5, 0.5, False),  # boundary p_revert == tau still reverts
        (0.2, 0.4, 0.5, True),  # p_revert < tau -> keep
        (0.8, 0.7, 0.5, True),  # p_revert <= p_keep -> keep
        (0.6, 0.6, 0.5, True),  # equal: not strictly greater -> keep
        (0.0, 0.0, 0.0, True),
    ],
)
def test_WB9_psa_revert_iff_prevert_ge_tau_and_gt_pkeep(p_keep, p_revert, tau, keep):
    """W-B9 (B12, Alg. 9): revert iff p_revert >= tau and p_revert > p_keep."""
    from p3net.v005.bartnik import psa_gom_keep

    assert psa_gom_keep(p_keep, p_revert, tau) is keep


def test_WB9_psa_history_grows_by_max_probability():
    """W-B9 (B12): every PSA decision appends max(p_keep, p_revert) to the
    probability history and reverts iff p_revert >= tau and > p_keep."""
    _, _, log = _run("MOPSA", budget=60)
    decisions = log.of("psa_decision")
    assert decisions
    prev = None
    for d in decisions:
        assert d["reverted"] == (d["p_revert"] >= d["tau"] and d["p_revert"] > d["p_keep"])
        assert math.isclose(d["appended"], max(d["p_keep"], d["p_revert"]))
        if prev is not None:
            assert d["history_len"] >= prev + 1
        prev = d["history_len"]


# ---------------------------------------------------------------------------
# Engine (event-based: observer hook, interfaces §7 Q-02)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("name", METHODS)
def test_WB1_no_hill_climber_new_solution_goes_to_level_0(name):
    """W-B1 (B3; Dushatskiy §2.3.4): no hill climber -- the new random
    solution is inserted into level 0 with no neighbour evaluations before."""
    _, _, log = _run(name)
    assert not log.of("fihc_end")
    segs = [s for s in _segments(log)]
    assert segs
    for seg in segs:
        inserts0 = [i for i, (k, p) in enumerate(seg) if k == "insert" and p["level"] == 0]
        if not inserts0:
            continue
        g = vals(seg[inserts0[0]][1]["genotype"])
        before = [vals(p["genotype"]) for k, p in seg[: inserts0[0]] if k == "eval"]
        assert all(sum(a != b for a, b in zip(x, g)) != 1 for x in before), (
            "neighbour evaluations before P0 (hill climber?)"
        )


@pytest.mark.parametrize("name", METHODS)
@pytest.mark.parametrize("budget", [50, 100])
def test_WB2_warmup_is_20_percent_all_real_before_first_training(name, budget):
    """W-B2 (B1, B-2 a): warm-up = 20 % of the budget (10 / 20 at b = 50 /
    100), all distinct and really evaluated before the first surrogate fit."""
    _, obj, log = _run(name, budget=budget)
    warm = budget // 5
    first_fit = next(i for i, (k, _) in enumerate(log) if k == "surrogate_fit")
    evals_before = [p for k, p in log[:first_fit] if k == "eval"]
    assert len(evals_before) == warm
    assert len({p["genotype"] for p in evals_before}) == warm
    assert log[first_fit][1]["n_points"] == warm


@pytest.mark.parametrize("name", METHODS)
def test_WB3_climbs_all_levels_promotes_only_when_compare_prefers(name):
    """W-B3 (B4): the solution is mixed with every level bottom-up (no
    break) and is added to L+1 only when Compare prefers the offspring."""
    _, _, log = _run(name, budget=100)
    n_levels = 0
    for seg in _segments(log)[:-1]:
        mixes = [p for k, p in seg if k == "level_mix"]
        assert [p["level"] for p in mixes][:n_levels] == list(range(n_levels))
        for i, (k, p) in enumerate(seg):
            if k == "insert" and p["level"] > 0:
                mix = [q for kk, q in seg[:i] if kk == "level_mix"][-1]
                assert mix["level"] == p["level"] - 1 and mix["compare"] > 0
            if k == "insert":
                n_levels = max(n_levels, p["level"] + 1)


@pytest.mark.parametrize("name", METHODS)
def test_WB4_donor_differs_on_F_when_one_exists(name):
    """W-B4 (B8, Alg. 9 l. 3): a GOM step leaves the solution unchanged only
    if no member of the level differs from it on F."""
    _, _, log = _run(name, budget=100)
    levels: dict[int, list[tuple]] = {}
    checked = 0
    for k, p in log:
        if k == "insert":
            levels.setdefault(p["level"], []).append(vals(p["genotype"]))
        elif k == "cluster_step":
            checked += 1
            if not p["changed"]:
                cur = vals(p["current"])
                F = list(p["cluster"])
                for d in levels.get(p["level"], []):
                    assert all(d[i] == cur[i] for i in F), (
                        "a differing donor existed but was not used"
                    )
    assert checked > 0


def test_WB5_dsa_real_evaluation_iff_gate_passes():
    """W-B5 (B10, Alg. 8; card N-1, Z-B1' of 2026-10-18 for MO-DSA): a
    changed candidate is really evaluated iff, on BOTH objectives, its
    prediction is strictly better (smaller) than the (1 - alpha)-quantile
    (numpy linear, Q-12) of the current model's predictions for the really
    evaluated solutions; alpha = 1 means better than all of them.
    `cluster_step` carries `alpha`, `thresholds` and `reference_predictions`
    (Q-41)."""
    from p3net.v005.bartnik import quantile_threshold

    _, _, log = _run("MODSA", budget=80)
    evaluated: list[tuple] = []
    events = list(log)
    checked = passed = 0
    for i, (k, p) in enumerate(events):
        if k == "eval":
            evaluated.append(p["genotype"])
            continue
        if k != "cluster_step" or not p["changed"] or p.get("prediction") is None:
            continue
        cand = vals(p["candidate"])
        # cluster_step is emitted after the step is resolved (Q-02), so its own
        # real evaluation, if any, is the event just before it.
        got_eval = i > 0 and events[i - 1][0] == "eval" and events[i - 1][1]["genotype"] == cand
        before = evaluated[:-1] if got_eval else evaluated
        if cand in set(before):
            continue
        alpha = float(p["alpha"])
        assert 0.0 < alpha <= 1.0
        ref = p["reference_predictions"]
        assert len(ref) == len(before), (
            "thresholds not computed over all really evaluated solutions"
        )
        for j in range(2):
            expected = quantile_threshold([r[j] for r in ref], 1.0 - alpha)
            assert math.isclose(p["thresholds"][j], expected, rel_tol=1e-9, abs_tol=1e-12)
        rule = all(p["prediction"][j] < p["thresholds"][j] for j in range(2))
        assert bool(p["gate_passed"]) == rule, "gate does not follow Z-B1'"
        assert got_eval == rule, "real evaluation does not follow the gate"
        checked += 1
        passed += rule
    assert checked > 0 and passed > 0


@pytest.mark.parametrize("name", METHODS)
def test_WB6_compare_uses_real_values_when_both_have_them(name):
    """W-B6 (B11, Alg. 8): when both solutions have real values, Compare is
    decided by them (dominance of real values fixes the outcome)."""
    _, _, log = _run(name, budget=100)
    checked = 0
    for p in log.of("level_mix"):
        a, b = p.get("after_real"), p.get("before_real")
        if a is None or b is None:
            continue
        if dominates(tuple(a), tuple(b)):
            assert p["compare"] > 0
            checked += 1
        elif dominates(tuple(b), tuple(a)):
            assert p["compare"] <= 0
            checked += 1
    assert checked > 0


@pytest.mark.parametrize("name", METHODS)
def test_WB11_surrogate_refit_after_every_real_evaluation(name):
    """W-B11 (B6): after the warm-up, every real evaluation is followed by a
    surrogate refit before the next real evaluation."""
    _, _, log = _run(name, budget=60)
    kinds = [k for k, _ in log]
    first_fit = kinds.index("surrogate_fit")
    pending = False
    for k in kinds[first_fit:]:
        if k == "eval":
            assert not pending, "two real evaluations without a refit in between"
            pending = True
        elif k == "surrogate_fit":
            pending = False


@pytest.mark.parametrize("name", METHODS)
def test_WB12_stops_after_1000_iterations_without_new_evaluation(name):
    """W-B12 (B7, 'exploration collapse'): on a space of 8 genotypes with
    budget 30 the method runs out of new solutions and stops after 1000
    consecutive iterations without a real evaluation, recording the reason."""
    space = space_of([2, 2, 2])
    log = EventLog()
    obj = CountingObjective(lambda g: 1.0 + sum(vals(g)), lambda g: 4.0 - sum(vals(g)), log=log)
    m = make(_cls(name), space, 30, 0, observer=log)
    drive(m, obj, 30)
    assert obj.n <= 8
    stops = log.of("stop")
    assert stops and "collapse" in str(stops[-1]["reason"]).lower()
    assert m.stop_reason == stops[-1]["reason"]
    last_eval = max(i for i, (k, _) in enumerate(log) if k == "eval")
    assert sum(1 for k, _ in log[last_eval:] if k == "iteration") in (1000, 1001)


@pytest.mark.parametrize("name", METHODS)
def test_WB13_two_independent_models_one_per_objective(name):
    """W-B13 (B16, B-1 a per-obj): two surrogate models are fitted, one per
    objective."""
    _, _, log = _run(name, budget=60)
    objs = {p["objective"] for p in log.of("surrogate_fit")}
    assert objs == {0, 1}


@pytest.mark.parametrize("name", METHODS)
def test_WB13_no_f2_access_and_budget(name):
    """W-B13 (O-B2, #6) and K-2: f2 is never read from the benchmark for
    unevaluated solutions (no hook in the constructor); the budget is spent
    exactly and never exceeded."""
    assert_no_benchmark_access(_cls(name))
    space = trap_space(3, 3, 3)
    obj = CountingObjective(trap_f1(3, 9), additive_cost(random_weights([3] * 9, seed=2)))
    drive(make(_cls(name), space, 50, 3), obj, 50)
    assert_budget_respected(obj, 50, exact=True)


def _segments(log):
    from ._support import iter_segments

    return iter_segments(log)


def test_guard_archive_reconstruction():
    """Helper guard: pareto_front on observed points is the B15 archive."""
    pts = [(1.0, 3.0), (2.0, 2.0), (3.0, 3.0)]
    assert sorted(pareto_front(pts, lambda x: x)) == [(1.0, 3.0), (2.0, 2.0)]
    assert random.Random(0).random() == random.Random(0).random()
