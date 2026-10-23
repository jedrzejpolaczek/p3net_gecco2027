"""Level-1 tests for the Bag-of-Baselines methods (card
`notes/plans/v005-sources/bag-of-baselines.md`, W-BB1-W-BB8).

Source: Guerrero-Viu et al., Bag of Baselines for Multi-objective Joint NAS
and HPO, AutoML@ICML 2021 (arXiv:2105.01015); code
github.com/automl/multi-obj-baselines (`shemoa.py`, `mobananas.py`, ...).
Card decisions: BB-2 a (faithful port), BB-3 (problem constants replaced),
BB-4 (initial size min(source, floor(0.25 b))), BB-5 (main track without
SH), A-1 / A-2 of `library-adapters.md` (EHVI = qNEHVI, MOTPE = optuna).
"""

from __future__ import annotations

import itertools
import math
import random

import pytest

from p3net.problem.objectives import fast_nondominated_sort

from ._support import (
    CountingObjective,
    G,
    additive_cost,
    assert_budget_respected,
    assert_no_benchmark_access,
    drive,
    drive_batches,
    hamming,
    make,
    random_weights,
    space_of,
    vals,
)


def _bob(name):
    from p3net.v005.baselines import bob

    return getattr(bob, name)


def _conflicting(domains, seed=0):
    """Two additive objectives with opposite trends (a real front)."""
    w1 = random_weights(domains, seed)
    w2 = [[1.0 - x for x in row] for row in w1]
    return CountingObjective(additive_cost(w1), additive_cost(w2))


# ---------------------------------------------------------------------------
# SH-EMOA (main track: steady-state EA without SH)
# ---------------------------------------------------------------------------


def test_WBB1_hv_contribution_remove_picks_smallest_contribution():
    """W-BB1 (SH2, HSSP with k = |F|-1): within the last front the point with
    the smallest hypervolume contribution is removed. Interior contributions
    do not depend on the reference point: B = (1, 9.999) contributes 0.0005;
    the extremes contribute >= 0.1 for any reference point beyond the nadir
    by >= 1 % of the range."""
    from p3net.v005.baselines.bob import hv_contribution_remove

    front = [(0.0, 10.0), (2.0, 0.0), (1.0, 9.999), (1.5, 5.0)]
    assert hv_contribution_remove(front) == 2


def test_WBB1_steady_state_one_offspring_per_step():
    """W-BB1 (SH1): after the initial population, SH-EMOA proposes exactly
    one offspring per step (steady state)."""
    batches = drive_batches(
        make(_bob("SHEMOA"), space_of([3] * 8), 100, 0), _conflicting([3] * 8), 100
    )
    assert len(batches[0]) == 20
    assert all(len(b) == 1 for b in batches[1:])


def test_WBB1_population_constant_and_removed_point_in_last_front():
    """W-BB1 (SH2): population size stays 20; the removed point belongs to
    the last NDS front of population + offspring."""
    from p3net.harness.runner import Observation, RunState

    space = space_of([3] * 8)
    obj = _conflicting([3] * 8)
    m = make(_bob("SHEMOA"), space, 80, 1)
    state = RunState()
    prev = None
    while state.evaluations_used < 80:
        props = m.propose(state)
        if not props:
            break
        new = [Observation(genotype=g, objectives=obj(g)) for g in props]
        state.history.extend(new)
        state.evaluations_used += len(new)
        m.update(state, new)
        pop = [vals(o) for o in m.population]
        assert len(pop) == 20
        if prev is not None:
            union = prev + [vals(g) for g in props]
            removed = [g for g in union if g not in pop]
            assert len(removed) == 1
            fronts = fast_nondominated_sort(union, lambda g: obj.value(g))
            assert removed[0] in fronts[-1], "removed point is not from the last front"
        prev = pop


def test_WBB2_get_budgets_matches_reference():
    """W-BB2 (SH3; `shemoa.py::get_budgets`): budgets from b_max down by
    ceil(b/eta) while > b_min; evaluations per budget grow x eta downwards.
    Reference values for (5, 25, 2, 15000, 100): budgets 7, 13, 25 and
    evaluations 8516, 4258, 2129."""
    from p3net.v005.baselines.bob import get_budgets

    budgets, evals = get_budgets(5, 25, 2, 15000, 100)
    assert [int(b) for b in budgets] == [7, 13, 25]
    assert [int(e) for e in evals] == [8516, 4258, 2129]
    budgets, evals = get_budgets(1, 27, 3, 1000, 20)
    assert [int(b) for b in budgets] == [3, 9, 27]
    assert all(int(evals[i]) == 3 * int(evals[i + 1]) for i in range(len(evals) - 1))


def _first(x):
    """A helper may return a child or a (child, child) pair."""
    return x[0] if isinstance(x, (tuple, list)) and not isinstance(x[0], int) else x


def test_WBB3_tournament_k3():
    """W-BB3 (SH4, BB-3; interfaces §7 Q-22 `shemoa_tournament(population,
    k, rng)`): tournament of k = 3 over the population ranked by NDS + HV
    contribution -- the unique best point wins with probability ~3/n
    (n = 10), the dominated-by-all point practically never."""
    from p3net.harness.runner import Observation
    from p3net.v005.baselines.bob import shemoa_tournament

    pts = [(0.0, 0.0)] + [(1.0 + i, 9.0 - i) for i in range(8)] + [(20.0, 20.0)]
    pop = [Observation(genotype=G(i), objectives=p) for i, p in enumerate(pts)]
    rng = random.Random(0)
    wins = {"best": 0, "worst": 0}
    trials = 3000
    for _ in range(trials):
        w = shemoa_tournament(pop, 3, rng)
        w = pop[w] if isinstance(w, int) else w
        if vals(w) == (0,):
            wins["best"] += 1
        if vals(w) == (9,):
            wins["worst"] += 1
    assert 0.22 < wins["best"] / trials < 0.36, wins
    assert wins["worst"] / trials < 0.005, wins


def test_WBB3_uniform_crossover_half_from_each_parent():
    """W-BB3 (SH4: uniform crossover p = 0.5): every gene comes from one of
    the parents, each parent with probability 0.5 per gene."""
    from p3net.v005.baselines.bob import uniform_crossover

    p1, p2 = G(*([0] * 20)), G(*([1] * 20))
    rng = random.Random(1)
    per_pos = [0] * 20
    trials = 2000
    for _ in range(trials):
        c = vals(_first(uniform_crossover(p1, p2, rng)))
        assert set(c) <= {0, 1}
        for i, v in enumerate(c):
            per_pos[i] += v
    assert all(0.44 < x / trials < 0.56 for x in per_pos), per_pos


def test_WBB3_mutation_redraws_n_mut_variables():
    """W-BB3 (SH4, BB-3: ceil(0.38 n) variables re-drawn): at most n_mut
    variables change; on average n_mut (k-1)/k (re-draw may hit the same
    value); every position can be chosen."""
    from p3net.v005.baselines.bob import shemoa_mutation

    n, k = 12, 6
    n_mut = math.ceil(0.38 * n)
    rng = random.Random(2)
    changed, touched = [], set()
    for _ in range(2000):
        g = tuple(rng.randrange(k) for _ in range(n))
        r = vals(shemoa_mutation(G(*g), [k] * n, n_mut, rng))
        assert all(0 <= v < k for v in r)
        d = [i for i in range(n) if g[i] != r[i]]
        assert len(d) <= n_mut
        changed.append(len(d))
        touched.update(d)
    mean = sum(changed) / len(changed)
    assert abs(mean - n_mut * (k - 1) / k) < 0.2, mean
    assert touched == set(range(n))


def test_WBB3_offspring_from_mutation_or_uniform_crossover():
    """W-BB3 (SH4, BB-3): every offspring is either a mutation of a member
    (at most ceil(0.38 n) variables re-drawn) or a uniform crossover of two
    members (each gene from one parent); both operators occur. n = 12,
    alphabet 6 so random genotypes almost never satisfy either condition."""
    n, k = 12, 6
    m_mut = math.ceil(0.38 * n)
    batches = drive_batches(
        make(_bob("SHEMOA"), space_of([k] * n), 70, 2), _conflicting([k] * n, 3), 70
    )
    seen = list(batches[0])
    kinds = set()
    for b in batches[1:]:
        child = b[0]
        mut = any(hamming(child, p) <= m_mut for p in seen)
        cx = any(
            all(c in (p[i], q[i]) for i, c in enumerate(child))
            for p, q in itertools.combinations(seen, 2)
        )
        assert mut or cx, (
            f"offspring {child} is neither a {m_mut}-mutation nor a crossover of members"
        )
        if mut and not cx:
            kinds.add("mutation")
        if cx and not mut:
            kinds.add("crossover")
        seen.append(child)
    assert kinds == {"mutation", "crossover"}


# ---------------------------------------------------------------------------
# MOTPE (optuna TPESampler) and EHVI (= qNEHVI)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("budget,startup", [(50, 10), (100, 10), (350, 10)])
def test_WBB4_motpe_configuration(budget, startup):
    """W-BB4 (MB2; library-adapters §3): gamma = 0.10 (optuna MOTPE default
    gamma), 24 EI candidates, random start of min(10, floor(0.25 b)) trials,
    good/bad split by MOTPE's own rule (multivariate=False)."""
    pytest.importorskip("optuna")
    from p3net.v005.baselines.library import MOTPE

    cfg = make(MOTPE, space_of([3] * 6), budget, 0).config()
    assert cfg["n_ei_candidates"] == 24
    assert cfg["n_startup_trials"] == startup
    assert cfg["multivariate"] is False
    gamma = cfg["gamma"]
    assert gamma(100) == math.ceil(0.10 * 100) if callable(gamma) else math.isclose(gamma, 0.10)


def test_WBB5_ehvi_is_qnehvi_with_independent_gps_one_point_per_step():
    """W-BB5 (ME1, #6; A-1 a): EHVI is realised by qLogNEHVI with an
    independent GP per objective (f2 modelled too) and one point per step."""
    pytest.importorskip("botorch")
    from p3net.v005.baselines.library import QNEHVI

    space = space_of([3, 3, 3])
    m = make(QNEHVI, space, 12, 0)
    cfg = m.config()
    assert "NEHVI" in str(cfg["acquisition"])
    assert cfg["n_models"] == 2 or cfg.get("model_per_objective") is True
    batches = drive_batches(m, _conflicting([3, 3, 3]), 12)
    assert all(len(b) == 1 for b in batches[1:])


# ---------------------------------------------------------------------------
# MO-BANANAS
# ---------------------------------------------------------------------------


def test_WBB6_mobananas_selects_four_per_iteration():
    """W-BB6 (MBa1; `get_MOBANANAS`: select 4): after the initial population
    each iteration evaluates `select` = 4 candidates (the last may be cut by
    the budget, K-2)."""
    batches = drive_batches(
        make(_bob("MOBANANAS"), space_of([3] * 6), 40, 0), _conflicting([3] * 6), 40
    )
    assert len(batches[0]) == 10
    assert all(len(b) == 4 for b in batches[1:-1])
    assert 1 <= len(batches[-1]) <= 4


def test_WBB6_mobananas_ensemble_and_selection_settings():
    """W-BB6 (MBa1-MBa2): ensemble of 5 networks trained 80 epochs (Adam,
    lr 0.1), NDS + crowding sorting, independent Thompson sampling,
    num_arch 8, select 4; standardised targets (BB-3)."""
    cfg = make(_bob("MOBANANAS"), space_of([3] * 6), 100, 0).config()
    assert cfg["ensemble_size"] == 5
    assert cfg["epochs"] == 80
    assert cfg["num_arch"] == 8
    assert cfg["select_models"] == 4
    assert cfg["target_scaling"] == "standardize"


# ---------------------------------------------------------------------------
# Shared: initial sizes, budget, f2 access
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "source,b,expected",
    [
        (50, 50, 12),
        (50, 100, 25),
        (50, 350, 50),
        (20, 50, 12),
        (20, 100, 20),
        (20, 350, 20),
        (100, 350, 87),
        (10, 39, 9),
        (10, 40, 10),
    ],
)
def test_WBB7_initial_design_size_rule(source, b, expected):
    """W-BB7 (BB-4): initial size = min(source value, floor(0.25 b))."""
    from p3net.v005.common import initial_design_size

    assert initial_design_size(source, b) == expected


@pytest.mark.parametrize(
    "budget,n_init,expected",
    [(50, 50, 12), (100, 50, 25), (350, 50, 50), (1000, 50, 50), (100, 20, 20)],
)
def test_WBB7_mobohb_initial_design_at_max_fidelity(budget, n_init, expected):
    """W-BB7 (BB-4, MO-BOHB row of 2026-10-20; authors' `get_MOBOHB(init=True)`,
    Q-43): the first batch of MO-BOHB is min(num_initial_samples,
    floor(0.25 b)) distinct random configurations, all at max fidelity E;
    num_initial_samples defaults to 50. MF ask-tell protocol: interfaces §7
    (Q-31)."""
    from p3net.harness.runner import RunState

    E = 27
    kw = {"max_epochs": E}
    if n_init != 50:
        kw["num_initial_samples"] = n_init
    m = make(_bob("MOBOHB"), space_of([4] * 8), budget, 0, **kw)
    first = m.propose(RunState())
    genos = [vals(g) for g, _ in first]
    assert len(first) == expected
    assert len(set(genos)) == expected
    assert all(int(e) == E for _, e in first), "initial design not at max fidelity"


def test_WBB7_mobohb_num_initial_samples_default():
    """W-BB7 (BB-4, Q-43): the constructor default of num_initial_samples is 50."""
    import inspect

    p = inspect.signature(_bob("MOBOHB").__init__).parameters
    assert p["num_initial_samples"].default == 50


@pytest.mark.parametrize("name,source", [("SHEMOA", 20), ("MOBANANAS", 20)])
@pytest.mark.parametrize("budget", [50, 100, 350])
def test_WBB7_first_batch_is_initial_design(name, source, budget):
    """W-BB7 (BB-4, interfaces §0: population methods propose the initial
    population in the first call): the first batch has min(source,
    floor(0.25 b)) distinct genotypes."""
    m = make(_bob(name), space_of([4] * 8), budget, 0)
    from p3net.harness.runner import RunState

    first = [vals(g) for g in m.propose(RunState())]
    assert len(first) == min(source, budget // 4)
    assert len(set(first)) == len(first)


@pytest.mark.parametrize("name", ["SHEMOA", "MOBANANAS"])
@pytest.mark.parametrize("budget", [37, 50])
def test_WBB7_budget_never_exceeded(name, budget):
    """W-BB7 (K-2, #35): exactly b real evaluations, no duplicates."""
    obj = _conflicting([3] * 7)
    drive(make(_bob(name), space_of([3] * 7), budget, 4), obj, budget)
    assert_budget_respected(obj, budget, exact=True)


@pytest.mark.parametrize("name", ["SHEMOA", "MOBANANAS", "MOSHBANANAS", "MOBOHB"])
def test_WBB8_no_access_to_f2_outside_evaluation(name):
    """W-BB8 (#6): no method takes the benchmark or an f2 function."""
    assert_no_benchmark_access(_bob(name))


def test_guard_conflicting_objective_has_a_front():
    obj = _conflicting([3] * 4)
    rng = random.Random(0)
    pts = [obj.value(tuple(rng.randrange(3) for _ in range(4))) for _ in range(50)]
    assert len(fast_nondominated_sort(pts, lambda p: p)[0]) > 1
