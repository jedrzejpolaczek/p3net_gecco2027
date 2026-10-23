"""Level-1 tests for the multi-fidelity track (card
`notes/plans/v005-sources/mf-track.md`, W-MF1-W-MF7).

Sources: Li et al., Hyperband, JMLR 2018 (pseudocode: s_max, n_i, r_i);
Li et al., ASHA, MLSys 2020; Schmucker et al. 2021 (MO-ASHA, NSGA-II
promotion). Card decisions: MF-1 a, MF-2 a, MF-3 a, MF-4.

MF ask-tell protocol (interfaces §7, Q-31): constructor
`(space, budget, rng, *, max_epochs)`, `propose(state) ->
list[tuple[Genotype, int]]` (genotype, epochs), answers as Observation in
the same order, `final_observations()` = observations at e = E.
"""

from __future__ import annotations

import math

import pytest

from p3net.harness.runner import Observation, RunState
from p3net.problem.objectives import crowding_distance, fast_nondominated_sort

from ._support import G, additive_cost, random_weights, space_of, vals


def _mf():
    from p3net.v005 import mf

    return mf


def test_WMF1_cost_is_resume_fraction():
    """W-MF1 (§2): a query (g, e) after e_prev epochs costs (e - e_prev) / E."""
    c = _mf().mf_cost
    assert math.isclose(c(7, 2, 200), 5 / 200)
    assert math.isclose(c(200, 0, 200), 1.0)
    assert math.isclose(c(12, 4, 12), 8 / 12)
    assert c(4, 4, 12) == 0.0


def _brackets(eta, r_min, R):
    out = []
    for br in _mf().bracket_schedule(eta, r_min, R):
        out.append([(int(n), int(round(r))) for n, r in br])
    return out


def test_WMF4_hyperband_brackets_match_li_et_al():
    """W-MF4 (Li et al. 2018, Alg. 1): eta = 3, R = 27 (r_min = 1):
    s_max = 3; bracket s starts with n = ceil((s_max+1)/(s+1) eta^s)
    configurations at r = R eta^-s; rungs n_i = floor(n eta^-i), r_i = r eta^i."""
    assert _brackets(3, 1, 27) == [
        [(27, 1), (9, 3), (3, 9), (1, 27)],
        [(12, 3), (4, 9), (1, 27)],
        [(6, 9), (2, 27)],
        [(4, 27)],
    ]


@pytest.mark.parametrize(
    "R,rungs", [(200, [2, 7, 22, 67, 200]), (12, [1, 4, 12]), (100, [1, 4, 11, 33, 100])]
)
def test_WMF7_hyperband_asha_ladders(R, rungs):
    """W-MF7 (MF-3: eta = 3, r_min = 1 epoch): JAHS 2, 7, 22, 67, 200;
    NAS-HPO-II 1, 4, 12; FCNet 1, 4, 11, 33, 100 (largest bracket)."""
    first = _brackets(3, 1, R)[0]
    assert [r for _, r in first] == rungs


@pytest.mark.parametrize("E,b_min", [(200, 40), (12, 3), (100, 20)])
def test_WMF7_bob_ladders_keep_source_ratio(E, b_min):
    """W-MF7 (MF-3 a): BoB methods use b_max = E, b_min = ceil(0.2 E)."""
    from p3net.v005.baselines.bob import get_budgets

    budgets, _ = get_budgets(math.ceil(0.2 * E), E, 2, 1000, 20)
    assert int(budgets[-1]) == E and int(budgets[0]) >= b_min


# ---------------------------------------------------------------------------
# Engine-level (MF ask-tell protocol, interfaces §7 Q-31)
# ---------------------------------------------------------------------------


class MFObjective:
    """f1 decreases with epochs; f2 = cost per epoch x epochs (MF-1 a)."""

    def __init__(self, domains, E):
        w = random_weights(domains, 0)
        self.f1 = additive_cost(w)
        self.per_epoch = additive_cost([[1.0 - x for x in row] for row in w])
        self.E = E
        self.calls: list[tuple[tuple, int]] = []

    def __call__(self, g, e):
        self.calls.append((vals(g), int(e)))
        return (self.f1(g) + 10.0 / (1 + e), self.per_epoch(g) * e / self.E)


def _mf_drive(m, obj, budget):
    state = RunState()
    spent, last = 0.0, {}
    for _ in range(100_000):
        props = m.propose(state)
        if not props:
            break
        new = []
        for g, e in props:
            spent += _mf().mf_cost(e, last.get(vals(g), 0), obj.E)
            last[vals(g)] = e
            new.append(Observation(genotype=g, objectives=obj(g, e)))
        state.history.extend(new)
        state.evaluations_used = math.floor(spent + 1e-9)
        m.update(state, new)
        if spent >= budget - 1e-9:
            break
    return spent


@pytest.mark.parametrize("name", ["HyperbandMO", "ASHAMO"])
def test_WMF1_total_cost_within_budget(name):
    """W-MF1 (§2, K-2): the summed cost never exceeds B full evaluations."""
    obj = MFObjective([3] * 6, 27)
    m = getattr(_mf(), name)(space_of([3] * 6), 20, __import__("random").Random(0), max_epochs=27)
    assert _mf_drive(m, obj, 20) <= 20 + 1e-9


@pytest.mark.parametrize("name", ["HyperbandMO", "ASHAMO"])
def test_WMF2_front_only_from_full_fidelity(name):
    """W-MF2 (§2): only evaluations at e = E enter the front and metrics."""
    obj = MFObjective([3] * 6, 27)
    m = getattr(_mf(), name)(space_of([3] * 6), 20, __import__("random").Random(1), max_epochs=27)
    _mf_drive(m, obj, 20)
    finals = m.final_observations()
    full = {g for g, e in obj.calls if e == 27}
    assert finals and all(vals(o.genotype) in full for o in finals)


def test_WMF3_f2_at_low_fidelity_is_observed_not_full():
    """W-MF3 (MF-1 a): the f2 a method receives at e < E is the e-epoch
    value; the promotion may extrapolate to E as per-epoch cost x E -- the
    method's extrapolation helper must equal f2_e * E / e, never a value
    read at E."""
    extrap = _mf().extrapolate_f2
    assert math.isclose(extrap(f2_at_e=3.0, e=3, E=27), 27.0)
    assert math.isclose(extrap(f2_at_e=0.5, e=1, E=12), 6.0)


def test_WMF5_asha_promotes_from_highest_rung_when_enough_candidates():
    """W-MF5 (ASHA, Li et al. 2020, Alg. 2 get_job): a configuration is
    promoted from the highest rung k that holds >= eta candidates with one of
    the top floor(n_k / eta) not yet promoted; otherwise a new configuration
    starts at the bottom rung."""
    asha = _mf().ASHAMO(space_of([3] * 4), 30, __import__("random").Random(0), max_epochs=27)
    obj = MFObjective([3] * 4, 27)
    state = RunState()
    rungs: dict[int, list[tuple]] = {}
    for _ in range(40):
        props = asha.propose(state)
        if not props:
            break
        ((g, e),) = props
        if rungs and e > min(rungs):
            lower = max(r for r in rungs if r < e)
            assert len(rungs[lower]) >= 3, "promotion from a rung with < eta candidates"
            assert vals(g) in rungs[lower], "promoted configuration was not in the rung below"
        else:
            assert not rungs or e == min(rungs), "new configuration not started at the bottom rung"
        rungs.setdefault(int(e), []).append(vals(g))
        o = Observation(genotype=g, objectives=obj(g, e))
        state.history.append(o)
        asha.update(state, [o])


def test_WMF6_promotion_by_nds_and_crowding():
    """W-MF6 (MF-2 a, MO-ASHA NSGA-II variant): the k promoted candidates of
    a rung are the first k by (NDS rank, -crowding distance)."""
    promote = _mf().promote_nsga2
    pts = [(1.0, 5.0), (2.0, 4.0), (3.0, 3.0), (4.0, 2.0), (5.0, 1.0), (4.0, 4.0), (5.0, 5.0)]
    chosen = sorted(promote(pts, 3))
    fronts = fast_nondominated_sort(list(range(len(pts))), lambda i: pts[i])
    f0 = fronts[0]
    cd = crowding_distance([pts[i] for i in f0], lambda p: p)
    ranked = sorted(range(len(f0)), key=lambda j: -cd[j])
    assert chosen == sorted(f0[j] for j in ranked[:3])
    assert set(chosen) <= set(f0)
    assert G(0) is not None
