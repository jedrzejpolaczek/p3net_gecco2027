"""Level-1 tests for REINFORCE with three multi-objective rewards (card
`notes/plans/v005-sources/reinforce.md`, W-R1-W-R8).

Sources: Williams 1992; NAS-Bench-201 reference implementation
`D-X-Y/AutoDL-Projects/exps/NAS-Bench-201-algos/reinforce.py` (factorised
policy, bias-corrected EMA baseline updated before the advantage, Adam);
Ying et al. 2019 (lr 0.5, Z-R1); MnasNet Eq. 2-3; MONAS Eq. 3; Chen et al.
2020 ADC (Eq. 3, Alg. 2) and cosine temperature with restarts (§4.3).
Card decisions: R-1 a, R-2 a, R-3 a (online min-max, Z-R2), R-4 a, R-5 a,
R-6 (ADC, period 0.2 b, T 25 -> 1, eps 0.1).
"""

from __future__ import annotations

import math
import random

import numpy as np
import pytest

from ._support import (
    CountingObjective,
    G,
    additive_cost,
    assert_budget_respected,
    drive,
    drive_batches,
    make,
    random_weights,
    space_of,
    vals,
)


def _m():
    from p3net.v005.baselines import reinforce

    return reinforce


def _obj(domains, seed=0):
    w1 = random_weights(domains, seed)
    w2 = [[1.0 - x for x in row] for row in w1]
    return CountingObjective(additive_cost(w1), additive_cost(w2))


# ---------------------------------------------------------------------------
# Rewards
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "a,c,T", [(0.9, 2.0, 1.0), (0.9, 0.5, 1.0), (0.7, 3.0, 3.0), (0.5, 10.0, 4.0)]
)
def test_WR3_mnasnet_soft_reward(a, c, T):
    """W-R3 (MnasNet Eq. 2-3, soft variant alpha = beta = -0.07): R =
    a * (c/T)^-0.07 on both sides of the target."""
    assert math.isclose(_m().reward_mnasnet(a, c, T), a * (c / T) ** -0.07, rel_tol=1e-12)


@pytest.mark.parametrize(
    "a,c,alpha", [(0.8, 0.3, 0.25), (0.8, 0.3, 0.75), (0.0, 1.0, 0.75), (1.0, 0.0, 0.25)]
)
def test_WR4_monas_mixed_reward(a, c, alpha):
    """W-R4 (MONAS Eq. 3): R = alpha * a - (1 - alpha) * c, a and c in [0, 1]."""
    assert math.isclose(
        _m().reward_monas(a, c, alpha), alpha * a - (1 - alpha) * c, rel_tol=1e-12, abs_tol=1e-12
    )


def test_WR5_adc_reward_hand_examples():
    """W-R5 (Chen et al. Eq. 3, Alg. 2: reward computed against the front
    BEFORE adding x; rho = Euclidean distance, interfaces §7 Q-27): non-dominated x:
    R = tanh((|P_f| + N_dominated_by_x) / C); dominated x:
    R = -tanh((N_dominating_x + rho_eps(x)) / C)."""
    adc = _m().reward_adc
    C, eps = 2.0, 0.1
    # objectives already in the normalised space; the front spans [0, 1] in
    # both objectives, so any front-based normalisation leaves them unchanged
    front = [(0.0, 1.0), (1 / 3, 2 / 3), (1.0, 0.0)]
    t = math.tanh
    assert math.isclose(adc((2 / 3, 1 / 3), front, eps, C), t((3 + 0) / C))  # new non-dominated
    assert math.isclose(adc((1 / 6, 0.5), front, eps, C), t((3 + 1) / C))  # dominates (1/3, 2/3)
    assert math.isclose(adc((2 / 3, 1.0), front, eps, C), -t((2 + 0) / C))  # dominated by 2 points
    assert math.isclose(adc((1.01, 0.01), front, eps, C), -t((1 + 1) / C))  # within eps of (1, 0)
    assert math.isclose(adc((4 / 3, 4 / 3), front, eps, C), -t((3 + 0) / C))  # dominated by all
    # Euclidean rho: distance 0.085 < eps (L1 would give 0.12 > eps)
    assert math.isclose(adc((1.06, 0.06), front, eps, C), -t((1 + 1) / C))


@pytest.mark.parametrize("period", [10, 70, 1200])
def test_WR6_cosine_temperature_with_restarts(period):
    """W-R6 (Chen et al. §4.3, R-6: T_max 25 -> T_min 1, period 0.2 b):
    T(t) = 1 + 12 * (1 + cos(pi * (t mod P) / P)); restart at t = P."""
    temp = _m().temperature
    expected = lambda t: 1 + 0.5 * 24 * (1 + math.cos(math.pi * (t % period) / period))  # noqa: E731
    for t in [0, 1, period // 2, period - 1, period, period + 1, 3 * period + period // 3]:
        assert math.isclose(temp(t, period), expected(t), rel_tol=1e-9)
    assert temp(0, period) == 25 and temp(period, period) == 25


def test_WR3_R4_online_minmax_normalisation():
    """R-3 a (Z-R2; also L-1 b): objectives normalised to [0, 1] by the
    current min/max of the evaluated points."""
    from p3net.v005.common import online_minmax

    norm = online_minmax([(2.0, 10.0), (4.0, 30.0), (3.0, 20.0)])
    assert norm((2.0, 30.0)) == (0.0, 1.0)
    assert norm((4.0, 10.0)) == (1.0, 0.0)
    a, b = norm((3.0, 15.0))
    assert math.isclose(a, 0.5) and math.isclose(b, 0.25)


def test_WR3_online_minmax_degenerate_objective_maps_to_zero():
    """R-3 a / L-1 b (interfaces §7 Q-33): when min == max for an objective,
    the normalised value of that objective is 0.0."""
    from p3net.v005.common import online_minmax

    norm = online_minmax([(2.0, 7.0), (4.0, 7.0)])
    assert norm((3.0, 7.0)) == (0.5, 0.0)
    assert online_minmax([(5.0, 1.0)])((5.0, 1.0)) == (0.0, 0.0)


# ---------------------------------------------------------------------------
# Policy and update
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("reward", ["mnasnet", "monas", "adc"])
def test_WR1_one_sample_per_step(reward):
    """W-R1 (R2): one architecture per step for every reward variant."""
    batches = drive_batches(
        make(_m().Reinforce, space_of([4] * 6), 30, 0, reward=reward), _obj([4] * 6), 30
    )
    assert batches and all(len(b) == 1 for b in batches)


def test_WR1_factorised_policy_small_initial_logits():
    """W-R1 (R1): a factorised policy -- one logit vector per variable, of
    length k_i -- initialised as 1e-3 * N(0, 1) (|logit| < 5e-3)."""
    domains = [4, 3, 5, 2]
    m = make(_m().Reinforce, space_of(domains), 30, 0)
    logits = [np.asarray(v, dtype=float) for v in m.logits]
    assert [len(v) for v in logits] == domains
    allv = np.concatenate(logits)
    assert np.all(np.abs(allv) < 5e-3) and np.std(allv) > 0


def test_WR2_baseline_updated_before_advantage_adam_lr_05():
    """W-R2 (R3, R4; reference `reinforce.py`: bias-corrected EMA,
    `baseline.update(r)` before `loss = -log pi * (r - baseline)`, then
    `optimizer.step()` on every step; torch Adam, lr 0.5, betas (0.9,
    0.999)): the first step has advantage r - r = 0, so the logits do not
    move, but the Adam step counter advances (Q-38). The first non-zero
    gradient, at Adam step t after t-1 zero-gradient steps, moves every logit
    by lr * (0.1 / (1 - 0.9^t)) / sqrt(0.001 / (1 - 0.999^t)) (0.372 at
    t = 2)."""
    from p3net.harness.runner import Observation, RunState

    domains = [3, 3, 3]
    m = make(_m().Reinforce, space_of(domains), 30, 0)
    obj = _obj(domains)
    state = RunState()
    snaps = [np.concatenate([np.asarray(v, float) for v in m.logits])]
    for _ in range(6):
        props = m.propose(state)
        new = [Observation(genotype=g, objectives=obj(g)) for g in props]
        state.history.extend(new)
        state.evaluations_used += len(new)
        m.update(state, new)
        snaps.append(np.concatenate([np.asarray(v, float) for v in m.logits]))
    assert np.allclose(snaps[1], snaps[0]), (
        "first step changed the policy: baseline not updated first"
    )
    t = next((i for i in range(1, len(snaps)) if not np.allclose(snaps[i], snaps[i - 1])), None)
    assert t is not None, "policy never updated"
    lr = 0.5
    expected = lr * (0.1 / (1 - 0.9**t)) / math.sqrt(0.001 / (1 - 0.999**t))
    assert np.allclose(np.abs(snaps[t] - snaps[t - 1]), expected, rtol=1e-4), (
        f"first non-zero Adam step (t = {t}) does not move every logit by {expected:.4f}"
    )


def test_WR3_mnasnet_target_constant_during_run():
    """W-R3 (R-4 a): T is a constant of the space during the run."""
    m = make(_m().Reinforce, space_of([3] * 4), 40, 0, reward="mnasnet", target=2.5)
    drive(m, _obj([3] * 4), 40)
    assert m.target == 2.5


def test_WR7_duplicates_free_and_budget():
    """W-R7 (#35): on a 9-genotype space a sampled duplicate is answered from
    H_t without consuming budget; the run never evaluates a genotype twice.
    A converged policy may stop early, but only as exploration collapse (#36,
    Q-39)."""
    obj = _obj([3, 3])
    m = make(_m().Reinforce, space_of([3, 3]), 8, 0)
    drive(m, obj, 8)
    assert len(set(obj.calls)) == len(obj.calls) <= 8
    _assert_full_or_collapse(m, obj, 8)


def test_WR7_policy_updated_on_duplicates():
    """W-R7: a duplicate still updates the policy (its reward comes from
    H_t): with 4 genotypes and budget 4, after the space is exhausted the
    method keeps learning from duplicates -- counted via the update log."""
    m = make(_m().Reinforce, space_of([2, 2]), 4, 0)
    obj = _obj([2, 2])
    drive(m, obj, 4)
    assert m.n_policy_updates > obj.n


@pytest.mark.parametrize("reward", ["mnasnet", "monas", "adc"])
@pytest.mark.parametrize("budget", [13, 50])
def test_WR8_budget_never_exceeded(reward, budget):
    """W-R8 (K-2): never more than b evaluations; fewer only when the run
    stopped on exploration collapse (#36; a converged policy at lr 0.5 keeps
    sampling duplicates, Q-39)."""
    obj = _obj([4] * 6)
    m = make(_m().Reinforce, space_of([4] * 6), budget, 1, reward=reward)
    drive(m, obj, budget)
    assert_budget_respected(obj, budget, exact=False)
    _assert_full_or_collapse(m, obj, budget)


def _assert_full_or_collapse(m, obj, budget):
    if obj.n < budget:
        assert "collapse" in str(getattr(m, "stop_reason", None)).lower(), (
            f"stopped at {obj.n} < {budget} without an exploration-collapse stop_reason"
        )
        assert m.propose(_empty_state_like(obj)) == [], "method stopped but still proposes"


def _empty_state_like(obj):
    from p3net.harness.runner import Observation, RunState

    hist = [Observation(genotype=G(*g), objectives=obj.value(g)) for g in obj.calls]
    return RunState(history=hist, evaluations_used=len(hist))


def test_guard_rng_independence():
    assert random.Random(0).random() != random.Random(1).random()
    assert vals((1, 2)) == (1, 2)
