"""Level-1 tests for canonical P3 without a surrogate (card
`notes/plans/v005-sources/p3-canonical.md`, W-K1-W-K6; W1-W16 are shared
with `test_p3net.py`, parametrised over both engines there).

Source: Goldman & Punch, GECCO'14 (P22, P25 literally: every changing mixing
step is one real evaluation). Decisions K-1 a (same engine as P3Net with an
exchangeable step evaluator), K-2 a (stop immediately at the b-th real
evaluation).
"""

from __future__ import annotations

import math
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


# --- W-K6 (claim C-46; interfaces supplement 2026-11-17, round 9) ---

SURROGATE_ENGINES = ["P3Net", "P3NetGate", "P3NetNoLink"]
# Seeds 2, 22 and 23 (of 0..39) are excluded: there the 64-bit draw is absorbed
# by rejection sampling in randrange (the shifted and unshifted Mersenne
# streams resynchronise), so canonical P3 has the same history with and
# without the draw and the negative control W-K6 b cannot hold (QUESTIONS.md
# Q-52).
WK6_SEEDS = [0, 1, 3]
# trap 3 x 3 x 3: n = 9, k = 3 -> one FIHC pass proposes sum(k_i - 1) = 18
# distinct neighbours (all differ from each other within the first pass), so a
# budget of 18 ends inside the first FIHC (P2) -- before any mixing step
# (P4 comes only after P2, card p3net.md Fig. 1) and before the surrogate is
# ever used (S-9 a: only after the first completed FIHC).
WK6_BUDGET = sum(k - 1 for k in [3] * 9)


def _history(cls, rng, **kw):
    obj = _obj()
    drive(cls(trap_space(3, 3, 3), WK6_BUDGET, rng, **kw), obj, WK6_BUDGET)
    assert obj.n == WK6_BUDGET
    return obj.calls


def _shifted(seed):
    r = random.Random(seed)
    r.getrandbits(64)
    return r


@pytest.mark.parametrize("engine", SURROGATE_ENGINES)
@pytest.mark.parametrize("seed", WK6_SEEDS)
def test_WK6_history_equals_canonical_after_one_draw(engine, seed):
    """W-K6 a (C-46): before the first mixing step, P3Net / P3NetGate /
    P3NetNoLink on Random(s) evaluate exactly the same genotypes, in the same
    order, as canonical P3 on Random(s) from which one getrandbits(64) was
    taken first (the surrogate's seed). Budget 18 = one FIHC pass on the
    3 x 3 x 3 trap, so no mixing step happens (see WK6_BUDGET)."""
    from p3net.v005 import methods

    method = _history(getattr(methods, engine), random.Random(seed))
    canonical = _history(methods.P3Canonical, _shifted(seed))
    assert method == canonical


@pytest.mark.parametrize("engine", SURROGATE_ENGINES)
@pytest.mark.parametrize("seed", WK6_SEEDS)
def test_WK6_without_the_draw_histories_differ(engine, seed):
    """W-K6 b (negative control): without that draw the histories of canonical
    P3 and the surrogate method differ on the same seed -- the test above
    would be vacuous if the surrogate did not consume rng."""
    from p3net.v005 import methods

    method = _history(getattr(methods, engine), random.Random(seed))
    canonical = _history(methods.P3Canonical, random.Random(seed))
    assert method != canonical


@pytest.mark.parametrize("engine", SURROGATE_ENGINES)
@pytest.mark.parametrize("seed", WK6_SEEDS)
def test_WK6_init_takes_exactly_one_getrandbits64(engine, seed):
    """W-K6 c (interfaces round 9): after __init__ the rng state equals a copy
    advanced by exactly one getrandbits(64)."""
    from p3net.v005 import methods

    r = random.Random(seed)
    getattr(methods, engine)(trap_space(3, 3, 3), WK6_BUDGET, r)
    assert r.getstate() == _shifted(seed).getstate()


@pytest.mark.parametrize(
    "engine,kw",
    [
        ("P3Canonical", {}),
        ("P3Net", {"step_evaluator": "oracle"}),
        ("P3Net", {"step_evaluator": "real"}),
    ],
)
@pytest.mark.parametrize("seed", WK6_SEEDS)
def test_WK6_no_draw_without_surrogate(engine, kw, seed):
    """W-K6 c (interfaces round 9): canonical P3 and P3Net without a
    surrogate (oracle / real step evaluator) leave rng untouched in __init__."""
    from p3net.v005 import methods

    r = random.Random(seed)
    getattr(methods, engine)(trap_space(3, 3, 3), WK6_BUDGET, r, **kw)
    assert r.getstate() == random.Random(seed).getstate()


# --- W17 (card p3net.md D-3 a, claim C-48; interfaces supplement 2026-11-17, round 10) ---

REJECT_ALL = (1e9, 1e9)  # dominated by every log-scale value: the gate rejects
ACCEPT_ALL = (-1e9, -1e9)  # dominates every log-scale value: the gate passes
# 3 x 3 x 3 trap: one FIHC costs 18..~60 evaluations, so 300 gives several
# iterations, each mixing with level 0 (and higher levels when they exist);
# test_W17_b checks that the canonical run really spends evaluations in mixing.
W17_BUDGET = 300
_MIX_EVENTS = ("cluster_step", "level_mix")


def _gate_run(seed, prediction, budget=W17_BUDGET):
    """P3NetGate on Random(seed) with fit -> no-op and predict_chain -> a
    constant (interfaces round 10). Returns (objective, event log, calls to
    predict_chain as (anchor genotype, chain length, evaluated-so-far?))."""
    from p3net.v005.methods import P3NetGate

    log = EventLog()
    obj = _obj(log)
    m = P3NetGate(trap_space(3, 3, 3), budget, random.Random(seed), observer=log)
    calls = []

    def predict_chain(anchor, chain):
        chain = list(chain)
        calls.append((vals(anchor.genotype), len(chain), vals(anchor.genotype) in set(obj.calls)))
        return prediction

    m.surrogate.fit = lambda *a, **k: None
    m.surrogate.predict_chain = predict_chain
    drive(m, obj, budget)
    return obj, log, calls


def _mixing_evals(log):
    """Real evaluations that happen after a fihc_end and before a later
    mixing event (cluster_step / level_mix) of the same iteration -- i.e.
    evaluations spent by mixing. Evaluations after the last mixing event and
    before the next fihc_end are the next new random solution and its FIHC.
    Steps are reported after they are resolved (Q-02), so a step's own
    evaluation precedes its cluster_step."""
    mixing, pending, open_ = [], [], False
    for k, p in log:
        if k == "fihc_end":
            pending, open_ = [], True
        elif k == "eval" and open_:
            pending.append(p["genotype"])
        elif k in _MIX_EVENTS and open_:
            mixing.extend(pending)
            pending = []
    return mixing


def _changed_steps(log):
    return [p for k, p in log if k == "cluster_step" and p["changed"]]


@pytest.mark.parametrize("seed", WK6_SEEDS)
def test_W17_a_gate_rejecting_everything_spends_nothing_in_mixing(seed):
    """W17 a (D-3 a, C-48): with a prediction dominated by every value the
    gate rejects every mixing step -- no step is accepted, no real evaluation
    comes from mixing (only new random solutions and FIHC are evaluated), and
    the solution after mixing equals the solution before it. The gate is
    really consulted (predict_chain called, with a one-element chain anchored
    at a really evaluated solution)."""
    obj, log, calls = _gate_run(seed, REJECT_ALL)
    assert obj.n == W17_BUDGET
    steps = [p for k, p in log if k == "cluster_step"]
    assert _changed_steps(log), "no changing mixing step -- the test would be vacuous"
    assert all(p["accepted"] is False for p in steps), "a step rejected by the gate was accepted"
    assert _mixing_evals(log) == [], "a real evaluation was spent in mixing behind a closed gate"
    assert calls, "predict_chain was never called"
    assert all(n == 1 for _, n, _ in calls), "P3Net-gate chain must have exactly one element"
    assert all(ok for _, _, ok in calls), "anchor is not a really evaluated solution"
    fihc = None
    for k, p in log:
        if k == "fihc_end":
            fihc = vals(p["genotype"])
        elif k == "cluster_step":
            assert vals(p["current"]) == fihc, "the solution changed during mixing"
        elif k == "level_mix":
            assert vals(p["after"]) == vals(p["before"]) == fihc
            assert tuple(p["after_objectives"]) == tuple(p["before_objectives"])


@pytest.mark.parametrize("seed", WK6_SEEDS)
def test_W17_b_gate_accepting_everything_equals_canonical_after_one_draw(seed):
    """W17 b (D-3 a, C-48, with W-K6): with a prediction dominating every
    value the gate passes every step, so P3NetGate on Random(s) evaluates the
    same genotypes in the same order as P3Canonical on Random(s) after one
    getrandbits(64). Budget W17_BUDGET = 300 on the 3 x 3 x 3 trap: several
    iterations past the first FIHC; the canonical run is checked to spend
    real evaluations in mixing, so the equality covers mixing, not only FIHC
    (unlike W-K6 at budget 18)."""
    from p3net.v005.methods import P3Canonical

    gate, _, calls = _gate_run(seed, ACCEPT_ALL)
    log = EventLog()
    canonical = _obj(log)
    drive(
        P3Canonical(trap_space(3, 3, 3), W17_BUDGET, _shifted(seed), observer=log),
        canonical,
        W17_BUDGET,
    )
    assert _mixing_evals(log), "canonical P3 spent nothing in mixing -- raise W17_BUDGET"
    assert calls, "predict_chain was never called"
    assert gate.calls == canonical.calls, "histories diverge at evaluation " + str(
        next(
            (i for i, (x, y) in enumerate(zip(gate.calls, canonical.calls)) if x != y),
            min(len(gate.calls), len(canonical.calls)),
        )
    )


def _d1_accept(new, old, archive):
    """D-1 b (MO-GOMEA rule, card p3net.md §9): accept iff new dominates old,
    has the same objective values, or is not dominated by the elitist
    archive (the non-dominated real evaluations so far -- 'not dominated by
    the archive' equals 'not dominated by any earlier real evaluation')."""
    from p3net.problem.objectives import dominates

    return dominates(new, old) or new == old or not any(dominates(a, new) for a in archive)


@pytest.mark.parametrize("seed", WK6_SEEDS)
def test_W17_c_acceptance_decided_by_true_values(seed):
    """W17 c (D-3 a, D-1 b): with the gate passing everything, every changing
    mixing step is evaluated really (or taken from H_t, #35) and is accepted
    iff the candidate's true objectives satisfy D-1 against the current
    solution and the real evaluations made before it. The current solution
    is reconstructed from fihc_end and the accepted steps, so the test does
    not depend on whether `current` is reported before or after the step."""
    obj, log, _ = _gate_run(seed, ACCEPT_ALL)
    seen: list[tuple] = []
    cur = None
    n_accepted = n_rejected = 0
    events = list(log)
    for i, (k, p) in enumerate(events):
        if k == "eval":
            seen.append(p["genotype"])
        elif k == "fihc_end":
            cur = vals(p["genotype"])
        elif k == "cluster_step" and p["changed"]:
            cand = vals(p["candidate"])
            assert cur is not None
            assert vals(p["current"]) in (cur, cand if p["accepted"] else cur)
            assert cand in seen, "a changing step behind an open gate was not evaluated really"
            just_evaluated = events[i - 1][0] == "eval" and events[i - 1][1]["genotype"] == cand
            prior = seen[:-1] if just_evaluated else seen
            archive = [obj.value(g) for g in prior]
            ok = _d1_accept(obj.value(cand), obj.value(cur), archive)
            assert p["accepted"] is ok, (
                f"step accepted={p['accepted']} but D-1 on true values says {ok}"
            )
            if p["accepted"]:
                cur, n_accepted = cand, n_accepted + 1
            else:
                n_rejected += 1
    assert n_accepted > 0 and n_rejected > 0, "need both outcomes for a non-vacuous test"


# --- Z-G1 (card p3net.md under D-3, answer to Q-53, round 10b) ---


def _zg1_prediction(cand, anchor_log):
    """Prediction table known to the test: the mode depends only on the
    candidate; the value is placed relative to the anchor's true log
    objectives so that every case of D-1 b on predictions occurs."""
    mode = sum(v * 3**i for i, v in enumerate(cand)) % 5
    a0, a1 = anchor_log
    return {
        0: (a0 - 0.1, a1 - 0.1),  # dominates the current solution
        1: (a0, a1),  # equal to the current solution
        2: (a0 - 0.2, a1 + 0.2),  # incomparable, small trade-off
        3: (a0 + 0.3, a1 + 0.3),  # dominated by the current (an archive point)
        4: (a0 - 5.0, a1 + 0.05),  # incomparable, large gain in f1
    }[mode]


def _log(v):
    return (math.log(v[0]), math.log(v[1]))


def test_ZG1_gate_passes_iff_predicted_objectives_satisfy_D1():
    """Z-G1 (2)-(4): a changing mixing step passes the gate iff the predicted
    (log) objectives satisfy D-1 b against the TRUE (log) objectives of the
    current solution and the elitist archive (non-dominated real evaluations
    so far, in log). Observable: a candidate not in H_t is evaluated really
    iff it passes; a step is accepted iff it passes and its true values
    satisfy D-1 b. Z-G1 (4): a candidate already in H_t goes through the gate
    too -- with a rejecting prediction the step is not applied although its
    true value is known. Z-G1 (1): predict_chain is anchored at the current
    solution. Cases covered: prediction dominates the current / equals it /
    passes only by not being dominated by the archive / is dominated by an
    archive point; and (4)."""
    from p3net.problem.objectives import dominates
    from p3net.v005.methods import P3NetGate

    cases = dict.fromkeys(["dominates", "equal", "archive_only", "rejected", "in_H_rejected"], 0)
    n_anchored = 0
    for seed in WK6_SEEDS:
        log = EventLog()
        obj = _obj(log)
        m = P3NetGate(trap_space(3, 3, 3), W17_BUDGET, random.Random(seed), observer=log)
        anchors = []

        def predict_chain(anchor, chain, _obj=obj, _anchors=anchors, _log_=log):
            chain = list(chain)
            assert len(chain) == 1
            _anchors.append((len(_log_), vals(anchor.genotype)))
            return _zg1_prediction(vals(chain[0]), _log(_obj.value(anchor.genotype)))

        m.surrogate.fit = lambda *a, **k: None
        m.surrogate.predict_chain = predict_chain
        drive(m, obj, W17_BUDGET)

        events = list(log)
        seen: list[tuple] = []
        cur = None
        last_step = -1
        for i, (k, p) in enumerate(events):
            if k == "eval":
                seen.append(p["genotype"])
            elif k == "fihc_end":
                cur = vals(p["genotype"])
            elif k == "cluster_step":
                window = [g for pos, g in anchors if last_step < pos <= i]
                last_step = i
                assert all(g == cur for g in window), "predict_chain not anchored at current"
                if not p["changed"]:
                    continue
                n_anchored += len(window)
                cand = vals(p["candidate"])
                just_evaluated = events[i - 1][0] == "eval" and events[i - 1][1]["genotype"] == cand
                prior = seen[:-1] if just_evaluated else seen
                in_h = cand in prior
                archive = [_log(obj.value(g)) for g in prior]
                cur_log = _log(obj.value(cur))
                pred = _zg1_prediction(cand, cur_log)
                by_dom, by_eq = dominates(pred, cur_log), pred == cur_log
                by_arch = not any(dominates(a, pred) for a in archive)
                gate = by_dom or by_eq or by_arch
                true_ok = _d1_accept(obj.value(cand), obj.value(cur), [obj.value(g) for g in prior])
                if not in_h:
                    assert just_evaluated is gate, (
                        f"step {cand}: gate should {'pass' if gate else 'reject'} (pred {pred}, "
                        f"current {cur_log}) but evaluated={just_evaluated}"
                    )
                else:
                    assert not just_evaluated, "a genotype from H_t was evaluated again"
                assert p["accepted"] is (gate and true_ok), (
                    f"step {cand}: accepted={p['accepted']}, gate={gate}, true D-1={true_ok}"
                )
                if by_dom:
                    cases["dominates"] += 1
                elif by_eq:
                    cases["equal"] += 1
                elif by_arch:
                    cases["archive_only"] += 1
                else:
                    cases["rejected"] += 1
                if in_h and not gate and true_ok:
                    cases["in_H_rejected"] += 1
                if p["accepted"]:
                    cur = cand
        assert anchors, "predict_chain was never called"
    assert n_anchored > 0
    missing = [c for c, n in cases.items() if n == 0]
    assert not missing, f"cases not exercised: {missing} ({cases})"
