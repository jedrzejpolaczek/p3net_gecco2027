"""Level-1 tests for P3 / P3Net (card `notes/plans/v005-sources/p3net.md`, W1-W16).

Source: Goldman & Punch, Parameter-less Population Pyramid, GECCO'14,
pp. 785-792 (steps P1-P25 as numbered in the card). Card decisions: D-1 b
(dominance in FIHC and promotion; MO-GOMEA acceptance in mixing), D-2 a
(FIHC on real evaluations), D-3 b (P3Net: mixing on the surrogate, real
evaluation after each level).
"""

from __future__ import annotations

import math
import random

import pytest

from p3net.problem.objectives import dominates

from ._support import (
    CountingObjective,
    EventLog,
    G,
    additive_cost,
    assert_budget_respected,
    cards,
    diff_positions,
    drive,
    iter_segments,
    make,
    random_weights,
    space_of,
    trap_f1,
    trap_space,
    vals,
)

ENGINES = ["P3Canonical", "P3Net"]


def _engine(name: str):
    from p3net.v005 import methods

    return getattr(methods, name)


def _trap_objective(log=None, *, n_blocks=3, block_size=3, alphabet=3, single=False):
    n = n_blocks * block_size
    f1 = trap_f1(block_size=block_size, n=n)
    f2 = (lambda g: 1.0) if single else additive_cost(random_weights([alphabet] * n, seed=7))
    return CountingObjective(f1, f2, log=log)


def _run_with_events(engine: str, budget: int, seed: int = 0):
    space = trap_space(3, 3, 3)
    log = EventLog()
    obj = _trap_objective(log)
    m = make(_engine(engine), space, budget, seed, observer=log)
    drive(m, obj, budget)
    return m, obj, log


def _table(domains, rows):
    from p3net.v005.p3.linkage import FrequencyTable

    t = FrequencyTable(list(domains))
    for r in rows:
        t.add(G(*r))
    return t


def _clusters_as_sets(clusters):
    return [frozenset(c) for c in clusters]


# ---------------------------------------------------------------------------
# W1-W5: main loop and pyramid (P1-P8, Fig. 1, s. 786)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("engine", ENGINES)
def test_W1_one_new_solution_per_iteration_enters_P0_iff_not_in_hashset(engine):
    """W1 (P1, P3; Fig. 1 s. 786): each iteration creates exactly one new
    solution (one FIHC result); it is added to P0 iff it is not yet in the
    hashset."""
    _, _, log = _run_with_events(engine, budget=600 if engine == "P3Canonical" else 250)
    segs = iter_segments(log)[:-1]  # last iteration may be cut by the budget (K-2)
    assert len(segs) >= 3, "too few complete iterations to test W1"
    in_pyramid: set[tuple] = set()
    for seg in segs:
        fihc = [p for k, p in seg if k == "fihc_end"]
        assert len(fihc) == 1, "an iteration must create exactly one new (climbed) solution"
        new = vals(fihc[0]["genotype"])
        p0 = [vals(p["genotype"]) for k, p in seg if k == "insert" and p["level"] == 0]
        if new in in_pyramid:
            assert p0 == [], "a solution already in the hashset was added to P0"
        else:
            assert p0 == [new], "a new solution not in the hashset must be added to P0 once"
        in_pyramid.update(vals(p["genotype"]) for k, p in seg if k == "insert")


@pytest.mark.parametrize("engine", ENGINES)
def test_W2_solution_is_mixed_with_every_level_even_without_improvement(engine):
    """W2 (P4, P6; Fig. 1 has no `break`): the new solution is mixed with
    every existing level, also after a level at which it did not improve."""
    _, _, log = _run_with_events(engine, budget=1500 if engine == "P3Canonical" else 300)
    segs = iter_segments(log)[:-1]
    n_levels = 0
    saw_continue_after_no_improvement = False
    for seg in segs:
        mixed = [p["level"] for k, p in seg if k == "level_mix"]
        assert mixed[:n_levels] == list(range(n_levels)), (
            f"levels mixed {mixed} do not cover all {n_levels} existing levels in order"
        )
        assert mixed == list(range(len(mixed))), "levels must be visited bottom-up without gaps"
        mixes = [p for k, p in seg if k == "level_mix"]
        for a, b in zip(mixes, mixes[1:]):
            if not dominates(tuple(a["after_objectives"]), tuple(a["before_objectives"])):
                saw_continue_after_no_improvement = True
        for k, p in seg:
            if k == "insert":
                n_levels = max(n_levels, p["level"] + 1)
    assert n_levels >= 2, "run never built a second level; W2 not exercised"
    assert saw_continue_after_no_improvement, (
        "never observed mixing continue after a non-improving level"
    )


@pytest.mark.parametrize("engine", ENGINES)
def test_W3_promotion_only_on_dominance_and_only_if_not_in_hashset(engine):
    """W3 (P5; D-1 b: dominance at promotion): a solution is added to
    P_{i+1} iff mixing with P_i made it dominate its pre-mixing state and it
    is not in the hashset; P_{i+1} is created when missing (never skipping a
    level)."""
    _, _, log = _run_with_events(engine, budget=1500 if engine == "P3Canonical" else 300)
    in_pyramid: set[tuple] = set()
    n_levels = 0
    last_mix = None
    promotions = 0
    events = list(log)
    for idx, (kind, p) in enumerate(events):
        if kind == "level_mix":
            last_mix = p
            improved = dominates(tuple(p["after_objectives"]), tuple(p["before_objectives"]))
            after = vals(p["after"])
            nxt = next(
                ((k, q) for k, q in events[idx + 1 :] if k in ("insert", "level_mix", "iteration")),
                None,
            )
            promoted = nxt is not None and nxt[0] == "insert" and nxt[1]["level"] == p["level"] + 1
            if improved and after not in in_pyramid:
                assert promoted or nxt is None, "improved new solution was not promoted (P5)"
            if promoted:
                assert improved, "promotion without Pareto improvement (D-1 b)"
                assert vals(nxt[1]["genotype"]) == after
                assert after not in in_pyramid, "promotion of a solution already in the hashset"
        elif kind == "insert":
            lvl = p["level"]
            assert lvl <= n_levels, f"level {lvl} created while only {n_levels} exist"
            if lvl > 0:
                assert last_mix is not None and last_mix["level"] == lvl - 1
                promotions += 1
            in_pyramid.add(vals(p["genotype"]))
            n_levels = max(n_levels, lvl + 1)
        elif kind == "iteration":
            last_mix = None
    assert promotions > 0, "no promotion observed; W3 not exercised"


def test_W4_pyramid_add_rejects_solution_present_on_any_level():
    """W4 (P7; §2.2 s. 786 'the levels represent disjoint sets of unique
    solutions'): Pyramid.add returns False for a solution already in the
    hashset, whatever the level; levels stay disjoint."""
    from p3net.v005.p3.pyramid import Pyramid

    p = Pyramid()
    a, b = G(0, 1, 2), G(2, 1, 0)
    assert p.add(0, a) is True
    assert p.add(0, a) is False
    assert p.add(1, a) is False
    assert p.add(1, b) is True
    assert p.add(0, b) is False
    flat = [vals(x) for lvl in p.levels for x in lvl]
    assert sorted(flat) == sorted([vals(a), vals(b)])
    assert {vals(x) for x in p.hashset} == {vals(a), vals(b)}


@pytest.mark.parametrize("engine", ENGINES)
def test_W4_levels_disjoint_after_a_run(engine):
    """W4 (P7): after a run no solution appears twice in the pyramid and the
    hashset equals the union of the levels."""
    m, _, _ = _run_with_events(engine, budget=800 if engine == "P3Canonical" else 250)
    flat = [vals(x) for lvl in m.pyramid.levels for x in lvl]
    assert len(flat) == len(set(flat)), "a solution occurs twice in the pyramid"
    assert set(flat) == {vals(x) for x in m.pyramid.hashset}


def test_W5_pyramid_has_no_target_sizes():
    """W5 (P8, §2.2/§2.5: no population or level sizes): a level grows by
    exactly one per successful add, without any cap."""
    from p3net.v005.p3.pyramid import Pyramid

    p = Pyramid()
    rng = random.Random(0)
    added = set()
    while len(added) < 700:
        g = tuple(rng.randrange(4) for _ in range(8))
        if g in added:
            continue
        assert p.add(0, G(*g)) is True
        added.add(g)
        assert len(p.levels[0]) == len(added)
    assert len(p.levels) == 1


@pytest.mark.parametrize("engine", ENGINES)
def test_W5_level_sizes_equal_number_of_inserts(engine):
    """W5 (P8): in a run, |P_i| equals the number of solutions inserted into
    P_i (no resizing, no target size, no random filling)."""
    m, _, log = _run_with_events(engine, budget=800 if engine == "P3Canonical" else 250)
    inserted: dict[int, int] = {}
    for k, p in log:
        if k == "insert":
            inserted[p["level"]] = inserted.get(p["level"], 0) + 1
    assert [len(lvl) for lvl in m.pyramid.levels] == [
        inserted.get(i, 0) for i in range(len(m.pyramid.levels))
    ]


# ---------------------------------------------------------------------------
# W6: FIHC (P10-P12, §2.1 s. 786)
# ---------------------------------------------------------------------------


def _dominance_compare(objective):
    def compare(a, b):
        fa, fb = objective(a), objective(b)
        if dominates(fa, fb):
            return 1
        if dominates(fb, fa):
            return -1
        return 0

    return compare


@pytest.mark.parametrize("seed", range(5))
def test_W6_fihc_ends_in_local_optimum(seed):
    """W6 (P12; D-1: strict dominance; D-2 a): FIHC returns a point where no
    single-position change gives a strict (dominating) improvement."""
    from p3net.v005.p3.fihc import fihc

    space = trap_space(3, 3, 3)
    obj = _trap_objective()
    rng = random.Random(seed)
    start = space.sample_uniform(rng)
    res = fihc(start, _dominance_compare(obj), cards(space), random.Random(seed))
    r = vals(res)
    for i, k in enumerate(cards(space)):
        for v in range(k):
            if v == r[i]:
                continue
            nb = r[:i] + (v,) + r[i + 1 :]
            assert not dominates(obj.value(nb), obj.value(r)), f"move x{i}={v} still improves"


def test_W6_fihc_accepts_only_strict_improvement_and_stops_after_one_quiet_pass():
    """W6 (P11 'strict improvement', P12 'repeat until no change; positions
    checked since the last change are skipped'): on a flat landscape FIHC
    makes no move and stops after exactly one pass of sum(k_i - 1)
    comparisons."""
    from p3net.v005.p3.fihc import fihc

    domains = [3, 4, 2, 5]
    calls = []

    def compare(a, b):
        calls.append((vals(a), vals(b)))
        return 0

    start = G(1, 2, 0, 3)
    res = fihc(start, compare, domains, random.Random(3))
    assert vals(res) == vals(start), "a tie was accepted as a move"
    assert len(calls) == sum(k - 1 for k in domains)


# ---------------------------------------------------------------------------
# W7-W10: linkage (P13-P18, Eq. 1-2, Fig. 2 s. 786)
# ---------------------------------------------------------------------------

_ROWS_COPY = [(0, 0, 0), (0, 0, 1), (1, 1, 0), (1, 1, 1)]  # x1 == x0, x2 independent


def test_W7_entropy_matches_eq2_on_hand_example():
    """W7 (P14, Eq. 2): H from the frequency table; for the hand example
    H(x0,x1) = H(x0) (x1 copies x0) and H(x0,x2) = 2 H(x0) (independent)."""
    t = _table([2, 2, 2], _ROWS_COPY)
    h0 = t.entropy((0,))
    assert h0 > 0
    assert math.isclose(t.entropy((1,)), h0)
    assert math.isclose(t.entropy((0, 1)), h0)
    assert math.isclose(t.entropy((0, 2)), 2 * h0)


def test_W7_cluster_distance_matches_eq1_on_hand_example():
    """W7 (P14, Eq. 1): D(Ci,Cj) = 1/(|Ci||Cj|) sum [2 - (H(ci)+H(cj))/H(ci u cj)].
    Hand values: D({0},{1}) = 0, D({0},{2}) = 1, D({0},{1,2}) = (0+1)/2 = 0.5,
    D({0,1},{2}) = 1."""
    from p3net.v005.p3.linkage import cluster_distance

    t = _table([2, 2, 2], _ROWS_COPY)
    assert math.isclose(cluster_distance(t, (0,), (1,)), 0.0, abs_tol=1e-12)
    assert math.isclose(cluster_distance(t, (0,), (2,)), 1.0)
    assert math.isclose(cluster_distance(t, (0,), (1, 2)), 0.5)
    assert math.isclose(cluster_distance(t, (0, 1), (2,)), 1.0)


def test_W7_build_clusters_recovers_trap_blocks():
    """W7 (P14-P15, test on a problem with known structure): on a level whose
    solutions have strongly linked blocks (as P3 levels on k-ary traps do),
    every block appears as a cluster."""
    from p3net.v005.p3.linkage import build_clusters

    rng = random.Random(0)
    blocks = [(0, 1, 2), (3, 4, 5), (6, 7, 8)]
    rows = []
    for _ in range(300):
        g = [0] * 9
        for b in blocks:
            v = rng.randrange(3)
            for i in b:
                g[i] = v if rng.random() < 0.85 else rng.randrange(3)
        rows.append(tuple(g))
    t = _table([3] * 9, rows)
    cl = _clusters_as_sets(build_clusters(t, random.Random(1)))
    for b in blocks:
        assert frozenset(b) in cl, f"block {b} not recovered; clusters: {cl}"


def test_W8_useful_has_all_singletons_and_no_root():
    """W8 (P15, P18; Fig. 2): `useful` contains every singleton and does not
    contain the whole-genotype cluster."""
    from p3net.v005.p3.linkage import build_clusters

    rng = random.Random(0)
    rows = [tuple(rng.randrange(3) for _ in range(6)) for _ in range(300)]
    cl = _clusters_as_sets(build_clusters(_table([3] * 6, rows), random.Random(0)))
    for i in range(6):
        assert frozenset({i}) in cl, f"singleton {{{i}}} missing"
    assert frozenset(range(6)) not in cl, "root cluster (whole genotype) must be removed"
    assert len(cl) == 2 * 6 - 2, (
        "agglomeration of n singletons without D=0 gives 2n-2 useful clusters"
    )


def test_W9_clusters_with_zero_distance_removed():
    """W9 (P16): if D(Ci,Cj) = 0 when merged, Ci and Cj are removed from
    `useful` (x1 always equals x0, so {0} and {1} go; {0,1} stays)."""
    from p3net.v005.p3.linkage import build_clusters

    rng = random.Random(0)
    rows = []
    for _ in range(300):
        a = rng.randrange(3)
        rows.append((a, a, rng.randrange(3), rng.randrange(3), rng.randrange(3)))
    cl = _clusters_as_sets(build_clusters(_table([3] * 5, rows), random.Random(0)))
    assert frozenset({0}) not in cl and frozenset({1}) not in cl
    assert frozenset({0, 1}) in cl
    for i in (2, 3, 4):
        assert frozenset({i}) in cl


def test_W10_clusters_ordered_smallest_first_ties_random():
    """W10 (P17): clusters ordered from the smallest; equal sizes in random
    order (different rng seeds give different orders of the singletons)."""
    from p3net.v005.p3.linkage import build_clusters

    rng = random.Random(0)
    rows = [tuple(rng.randrange(3) for _ in range(7)) for _ in range(300)]
    t = _table([3] * 7, rows)
    singleton_orders = set()
    for seed in range(10):
        cl = build_clusters(t, random.Random(seed))
        sizes = [len(c) for c in cl]
        assert sizes == sorted(sizes), f"not smallest-first: {sizes}"
        singleton_orders.add(tuple(tuple(c) for c in cl if len(c) == 1))
    assert len(singleton_orders) > 1, "ties are never shuffled"


# ---------------------------------------------------------------------------
# W11-W13: mixing with a level (P20-P25, Fig. 3, s. 786-787)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("seed", range(10))
def test_W11_donor_differs_on_cluster(seed):
    """W11 (P21-P23, s. 787): donors are tried until one differs from the
    solution on the cluster; no 'no change' proposal is ever evaluated."""
    from p3net.v005.p3.mixing import mix_with_level

    g = G(0, 0, 0, 0)
    level = [G(0, 1, 1, 1)] * 6 + [G(2, 1, 1, 1)]  # only the last donor differs on cluster (0,)
    calls = []

    def accept(new, old):
        calls.append((vals(new), vals(old)))
        return True

    res = mix_with_level(g, level, [(0,)], accept, random.Random(seed))
    assert vals(res)[0] == 2, "the only donor that differs on F was not used"
    assert all(n != o for n, o in calls), "an unchanged solution was proposed/evaluated"


def test_W11_no_evaluation_when_no_donor_differs():
    """W11 (P23): if no donor differs on the cluster, nothing is evaluated."""
    from p3net.v005.p3.mixing import mix_with_level

    calls = []
    res = mix_with_level(
        G(1, 2, 0),
        [G(1, 2, 2), G(1, 2, 1)],
        [(0, 1)],
        lambda n, o: calls.append(1) or True,
        random.Random(0),
    )
    assert vals(res) == (1, 2, 0) and calls == []


def test_W12_rejected_change_reverted_accepted_change_kept():
    """W12 (P22, P24): a change the acceptance rule rejects is reverted; an
    accepted one (incl. a tie, P24) is kept."""
    from p3net.v005.p3.mixing import mix_with_level

    level = [G(1, 1, 1)]
    rej = mix_with_level(G(0, 0, 0), level, [(0,), (1, 2)], lambda n, o: False, random.Random(0))
    assert vals(rej) == (0, 0, 0)
    acc = mix_with_level(G(0, 0, 0), level, [(0,), (1, 2)], lambda n, o: True, random.Random(0))
    assert vals(acc) == (1, 1, 1)


def test_W12_mogomea_accept_rule():
    """W12 (P22, P24 with D-1 b, MO-GOMEA rule): accept iff the new solution
    dominates the old one, has the same objective values, or is not
    dominated by the elitist archive."""
    from p3net.v005.p3.mixing import mogomea_accept

    archive = [(1.0, 4.0), (2.0, 2.0), (4.0, 1.0)]
    assert mogomea_accept((1.5, 1.5), (2.0, 2.0), archive) is True  # dominates old
    assert mogomea_accept((3.0, 3.0), (3.0, 3.0), archive) is True  # tie (plateau drift, P24)
    assert (
        mogomea_accept((3.0, 3.0), (2.0, 2.0), archive) is False
    )  # worse than old, dominated by archive
    assert mogomea_accept((3.0, 1.5), (5.0, 5.0), archive) is True  # dominates old
    assert (
        mogomea_accept((0.5, 5.0), (2.5, 2.5), archive) is True
    )  # incomparable, not dominated by archive
    assert (
        mogomea_accept((3.0, 2.5), (2.5, 3.0), archive) is False
    )  # incomparable, dominated by (2,2)


def test_W13_at_most_one_evaluation_per_cluster():
    """W13 (P25, s. 787: 'each cluster costs at most one evaluation'): with
    many differing donors, the acceptance/evaluation is called at most once
    per cluster, and each call changes only that cluster."""
    from p3net.v005.p3.mixing import mix_with_level

    rng = random.Random(0)
    level = [G(*(rng.randrange(4) for _ in range(6))) for _ in range(30)]
    clusters = [(0,), (1,), (2,), (3,), (4,), (5,), (0, 1), (2, 3), (4, 5), (0, 1, 2, 3)]
    per_cluster: dict[frozenset, int] = {}

    def accept(new, old):
        changed = frozenset(diff_positions(new, old))
        owner = [c for c in clusters if changed and changed <= frozenset(c)]
        assert owner, f"change {set(changed)} is not within a single cluster"
        key = min((frozenset(c) for c in owner), key=len)
        per_cluster[key] = per_cluster.get(key, 0) + 1
        return rng.random() < 0.5

    mix_with_level(G(0, 0, 0, 0, 0, 0), level, clusters, accept, random.Random(5))
    assert sum(per_cluster.values()) <= len(clusters)


# ---------------------------------------------------------------------------
# W14-W15: evaluations (O-3, O-5)
# ---------------------------------------------------------------------------


def test_W14_p3net_real_evaluations_per_iteration():
    """W14 (O-3, D-3 b, D-2 a): in P3Net an iteration spends real evaluations
    only on FIHC and on one evaluation of the result after each level, so
    after FIHC: #real evaluations <= #levels mixed."""
    _, _, log = _run_with_events("P3Net", budget=400)
    segs = iter_segments(log)[:-1]
    assert segs
    for seg in segs:
        kinds = [k for k, _ in seg]
        assert "fihc_end" in kinds
        after_fihc = seg[kinds.index("fihc_end") + 1 :]
        n_eval = sum(1 for k, _ in after_fihc if k == "eval")
        n_levels = sum(1 for k, _ in after_fihc if k == "level_mix")
        assert n_eval <= n_levels, f"{n_eval} real evaluations for {n_levels} levels"


@pytest.mark.parametrize("engine", ENGINES)
def test_W15_every_real_evaluation_in_history_and_no_duplicates(engine):
    """W15 (O-5, #35): every real evaluation enters H_t; a genotype already
    in H_t never consumes budget again (small alphabet -> many revisits)."""
    space = trap_space(n_blocks=2, block_size=3, alphabet=2)  # 64 genotypes
    obj = _trap_objective(n_blocks=2, block_size=3, alphabet=2)
    budget = 30
    state = drive(make(_engine(engine), space, budget, 0), obj, budget)
    assert [vals(o.genotype) for o in state.history] == obj.calls
    assert_budget_respected(obj, budget, exact=False)


def test_W15_eval_cache_is_the_history():
    """W15 (O-5, #35): EvalCache stores H_t; get returns None for unseen
    genotypes; history lists every stored observation once."""
    from p3net.v005.common import EvalCache

    c = EvalCache()
    assert c.get(G(0, 1)) is None
    c.put(G(0, 1), (1.0, 2.0))
    c.put(G(1, 1), (3.0, 4.0))
    assert tuple(c.get(G(0, 1))) == (1.0, 2.0)
    hist = c.history()
    assert sorted((vals(o.genotype), tuple(o.objectives)) for o in hist) == [
        ((0, 1), (1.0, 2.0)),
        ((1, 1), (3.0, 4.0)),
    ]


# ---------------------------------------------------------------------------
# W16: P3 solves k-ary traps (whole algorithm)
# ---------------------------------------------------------------------------


def test_W16_p3_finds_trap_optimum_in_8_of_10_runs():
    """W16 (whole algorithm, real objective, no surrogate): canonical P3 with
    a single objective (f2 constant) finds the k-ary trap optimum in >= 8/10
    runs (seeds 0-9). Trap: 3 blocks x 3 variables, alphabet 3; budget 6000."""
    from p3net.v005.methods import P3Canonical

    space = trap_space(3, 3, 3)
    successes = 0
    opt = (0,) * 9

    def found(state):
        return bool(state.history) and vals(state.history[-1].genotype) == opt

    for seed in range(10):
        obj = _trap_objective(single=True)
        drive(make(P3Canonical, space, 6000, seed), obj, 6000, until=found)
        if opt in set(obj.calls):
            successes += 1
    assert successes >= 8, f"optimum found in {successes}/10 runs"


def test_space_helpers_sanity():
    """Guard for the test helpers themselves: the trap optimum is all zeros
    with f1 == 1 and every other genotype is worse."""
    f = trap_f1(3, 9)
    assert f((0,) * 9) == 1.0
    rng = random.Random(0)
    for _ in range(200):
        g = tuple(rng.randrange(3) for _ in range(9))
        if g != (0,) * 9:
            assert f(g) > 1.0
    assert cards(space_of([2, 3])) == [2, 3]
