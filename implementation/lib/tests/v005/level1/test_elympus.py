"""Level-1 tests for eLyMPuS on real evaluations (card
`notes/plans/v005-sources/elympus.md`, W-E1-W-E13 and W-E7b).

Source: Przewozniczek, Chicano, Tinos, Komarnicki, Limited Perfect
Monotonical Surrogates constructed using Variable Interaction Graphs,
GECCO'26, pp. 647-651 (Pseudocode 1-5, Theorem 1); reference code
github.com/przewooz/OLyMPuS. Card decisions: E-1 a (P3 with FIHC-eLyMPuS),
E-2 a (one eLyMPuS per objective), E-3 a (final FIHC solution really
evaluated), Z-E1 (k-ary entry = ordering of all k values), Z-E3 (1/x rules
of the code), Z-E5 (move only on strict improvement / dominance).

Conventions (interfaces §7, Q-14): `partial_compare(..., evaluate,
...)` gets a scalar evaluate (the objective of that eLyMPuS instance) and
returns > 0 iff x with `var := value` is strictly better (smaller) than x;
`fihc_elympus(..., evaluate, ...)` gets evaluate returning (f1, f2).
"""

from __future__ import annotations

import copy
import itertools
import math
import random

import pytest

from p3net.problem.objectives import dominates
from p3net.problem.synthetic_kary import true_dependency_graph

from ._support import (
    CountingObjective,
    G,
    additive_cost,
    drive,
    make,
    random_weights,
    trap_f1,
    trap_space,
    vals,
)

NB, BS, K = 3, 3, 3
N = NB * BS


class Counter:
    """Scalar or vector evaluate that counts calls and can refuse to go on."""

    def __init__(self, f, cap: int | None = None):
        self.f, self.n, self.cap = f, 0, cap

    def __call__(self, g):
        self.n += 1
        if self.cap is not None and self.n > self.cap:
            raise RuntimeError(f"more than {self.cap} evaluations: FIHC does not terminate")
        return self.f(vals(g))


class NeverVerify:
    def start_call(self, vig_empty):
        return False

    def end_call(self, found_dependency, repeated_optimum):
        pass


class AlwaysVerify(NeverVerify):
    def start_call(self, vig_empty):
        return True


def _el(domains, seed=0):
    from p3net.v005.elympus import ELyMPuS

    return ELyMPuS(list(domains), random.Random(seed))


def _set_vig(el, graph):
    for i in list(el.vig):
        el.vig[i].clear()
    for i, nb in graph.items():
        el.vig.setdefault(i, set()).update(nb)


def _edges(el):
    return {frozenset((i, j)) for i, nb in el.vig.items() for j in nb if i != j}


def _sign(x):
    return (x > 0) - (x < 0)


F1 = trap_f1(BS, N)
F2 = additive_cost(random_weights([K] * N, seed=4))
TRUE_EDGES = {
    frozenset((i, j)) for i, nb in true_dependency_graph(NB, BS).items() for j in nb if i != j
}


def _vec(g):
    return (F1(g), F2(g))


# ---------------------------------------------------------------------------


def test_WE1_vig_empty_at_start():
    """W-E1 (E1; v005: no domain knowledge): the VIG starts empty."""
    el = _el([K] * N)
    assert all(len(s) == 0 for s in el.vig.values())


def test_WE2_hit_costs_nothing_miss_costs_real_evaluations():
    """W-E2 (E2, Pseudocode 1-2): a hit in the pair list does not call the
    benchmark; a miss evaluates really and stores a pair."""
    el = _el([K] * N)
    ev = Counter(F1)
    x = (1, 2, 0, 1, 1, 2, 0, 0, 1)
    el.partial_compare(G(*x), 0, 2, ev, False)
    assert ev.n > 0, "a miss must evaluate"
    n = ev.n
    x2 = (1, 0, 2, 2, 0, 1, 1, 2, 0)  # differs elsewhere; empty VIG => empty context => hit
    el.partial_compare(G(*x2), 0, 2, ev, False)
    assert ev.n == n, "a hit called the benchmark"
    el.partial_compare(G(*x2), 4, 2, ev, False)
    assert ev.n > n, "a miss for another variable must evaluate"


@pytest.mark.parametrize("k", [2, 4])
def test_WE7b_entry_orders_all_k_values_from_one_fihc_step(k):
    """W-E7b (Z-E1): one miss on (g, context) costs at most k evaluations (one
    FIHC step on g) and stores the ordering of all k values: every other
    value of g is then compared for free and correctly; k = 2 behaves like
    the binary code (one pair per variable and context)."""
    w = random_weights([k] * 4, seed=11)
    f = additive_cost(w)
    el = _el([k] * 4)
    ev = Counter(f)
    x = (0,) * 4
    el.partial_compare(G(*x), 1, 1, ev, False)
    assert 2 <= ev.n <= k
    n = ev.n
    for xx in [(0, 0, 0, 0), (1, 1, 1, 1), (1, k - 1, 0, 1)]:
        for v in range(k):
            if v == xx[1]:
                continue
            r = el.partial_compare(G(*xx), 1, v, ev, False)
            yv = list(xx)
            yv[1] = v
            assert _sign(r) == _sign(f(xx) - f(tuple(yv))), "stored ordering wrong"
    assert ev.n == n, "values of g other than the first one were not covered by the entry"


def test_WE3_full_true_vig_list_answers_always_correct():
    """W-E3 (E5, Theorem 1): with the full true VIG of the k-ary trap, every
    answer taken from the pair lists equals a freshly computed comparison."""
    true = true_dependency_graph(NB, BS)
    warm = _el([K] * N)
    _set_vig(warm, true)
    rng = random.Random(0)
    ev = Counter(F1)
    for _ in range(400):
        x = G(*(rng.randrange(K) for _ in range(N)))
        var = rng.randrange(N)
        val = rng.choice([v for v in range(K) if v != vals(x)[var]])
        cold = _el([K] * N)
        _set_vig(cold, true)
        assert _sign(warm.partial_compare(x, var, val, ev, False)) == _sign(
            cold.partial_compare(x, var, val, Counter(F1), False)
        )


def test_WE4_discovered_edges_are_true_dependencies():
    """W-E4 (E6, E7): every edge eLyMPuS adds is a true dependency (zero false
    edges on the k-ary trap with known VIG; additive f2 gets none)."""
    from p3net.v005.elympus import OneOverX, fihc_elympus

    el1, el2 = _el([K] * N, 1), _el([K] * N, 2)
    sched = OneOverX()
    rng = random.Random(3)
    ev = Counter(_vec, cap=200_000)
    for s in range(25):
        x = G(*(rng.randrange(K) for _ in range(N)))
        fihc_elympus(x, (el1, el2), ev, sched, random.Random(s))
    assert _edges(el1) <= TRUE_EDGES, f"false edges: {_edges(el1) - TRUE_EDGES}"
    assert _edges(el2) == set(), "dependencies found for an additive objective"


def _interaction_problem():
    # binary n = 8; only x0 and x5 interact: d f / d x0 = -1 if x5 == 0 else +2
    w = [0.0, 0.3, 0.5, 0.7, 0.2, 0.1, 0.4, 0.6]

    def f(x):
        x = vals(x)
        return 10.0 + 3.0 * x[0] * x[5] - 1.0 * x[0] + sum(w[i] * x[i] for i in range(1, 8))

    return f


def test_WE5_recursive_ll_finds_the_missing_dependency():
    """W-E5 (E6, Pseudocode 3): for two solutions with equal context of
    g and different comparison results, RecursiveLL returns the variable
    responsible and adds the edge in both directions."""
    el = _el([2] * 8)
    x1 = G(0, 0, 0, 0, 0, 0, 0, 0)
    x2 = G(0, 1, 1, 1, 1, 1, 1, 1)
    v, _ = el.recursive_ll(x1, x2, 0, Counter(_interaction_problem()))
    assert v == 5
    assert 5 in el.vig[0] and 0 in el.vig[5]
    assert _edges(el) == {frozenset((0, 5))}


def test_WE5_recursive_ll_needs_at_most_log2_D_splits():
    """W-E5 (E6: one missing dependency in <= ceil(log2 |D|) steps; interfaces
    §7 Q-15: recursive_ll returns (var, n_splits)): |D| = 7 -> at most 3
    splits."""
    el = _el([2] * 8)
    v, n_splits = el.recursive_ll(
        G(0, 0, 0, 0, 0, 0, 0, 0), G(0, 1, 1, 1, 1, 1, 1, 1), 0, Counter(_interaction_problem())
    )
    D = 7
    assert v == 5
    assert 1 <= n_splits <= math.ceil(math.log2(D))


def test_WE6_pairs_stored_before_vig_update_stay_valid():
    """W-E6 (E4): pairs added before the VIG grows remain in use: after adding
    the edge 0-1, a query whose new context (x1) matches the stored solution
    is still a hit; one that does not match is a miss."""
    el = _el([3] * 4)
    ev = Counter(additive_cost(random_weights([3] * 4, seed=5)))
    el.partial_compare(G(0, 0, 0, 0), 0, 1, ev, False)
    el.vig.setdefault(0, set()).add(1)
    el.vig.setdefault(1, set()).add(0)
    n = ev.n
    el.partial_compare(G(0, 0, 2, 2), 0, 1, ev, False)
    assert ev.n == n, "old pair was dropped after the VIG update"
    el.partial_compare(G(0, 2, 0, 0), 0, 1, ev, False)
    assert ev.n > n, "context x1 changed but the old pair was still used"


# --- W-E7: 1/x verification schedule (E8, Z-E3) ---


def _flags(s, n, vig_empty=False):
    out = []
    for _ in range(n):
        f = s.start_call(vig_empty)
        s.end_call(False, False)
        out.append(bool(f))
    return out


def _gaps(flags):
    idx = [i for i, f in enumerate(flags) if f]
    return [b - a - 1 for a, b in zip(idx, idx[1:])]


def test_WE7_always_verify_while_vig_empty():
    """W-E7 (Z-E3 rule 1): verification always happens while the VIG is empty."""
    from p3net.v005.elympus import OneOverX

    assert all(_flags(OneOverX(), 50, vig_empty=True))


def test_WE7_gap_grows_by_one_after_each_fruitless_verification():
    """W-E7 (E8, 1/x): with no dependency found, the number of calls without
    verification between consecutive verifications grows by exactly one."""
    from p3net.v005.elympus import OneOverX

    gaps = _gaps(_flags(OneOverX(), 300))
    assert len(gaps) >= 8
    assert all(b - a == 1 for a, b in zip(gaps, gaps[1:])), gaps


def test_WE7_verify_right_after_a_discovery():
    """W-E7 (Z-E3 rule 2): the call following one that discovered a
    dependency always verifies."""
    from p3net.v005.elympus import OneOverX

    s = OneOverX()
    _flags(s, 60)  # long fruitless history: large gap
    while not s.start_call(False):
        s.end_call(False, False)
    s.end_call(True, False)  # this verifying call found a dependency
    assert s.start_call(False) is True


def test_WE7_repeated_optimum_resets_counter():
    """W-E7 (Z-E3 rule 3): reaching an already found local optimum resets the
    counter -- afterwards the schedule behaves like a fresh one."""
    from p3net.v005.elympus import OneOverX

    fresh = _flags(OneOverX(), 40)
    s = OneOverX()
    _flags(s, 80)
    s.start_call(False)
    s.end_call(False, True)
    assert _flags(s, 40) == fresh


@pytest.mark.parametrize("seed", range(4))
def test_WE8_fihc_elympus_ends_in_local_optimum_with_full_vig(seed):
    """W-E8 (E9, Z-E5): with full true VIGs, FIHC-eLyMPuS ends where no
    single-variable change dominates on the true function."""
    from p3net.v005.elympus import OneOverX, fihc_elympus

    el1, el2 = _el([K] * N), _el([K] * N)
    _set_vig(el1, true_dependency_graph(NB, BS))
    rng = random.Random(seed)
    x = G(*(rng.randrange(K) for _ in range(N)))
    r = vals(
        fihc_elympus(x, (el1, el2), Counter(_vec, cap=100_000), OneOverX(), random.Random(seed))
    )
    for i in range(N):
        for v in range(K):
            if v != r[i]:
                nb = r[:i] + (v,) + r[i + 1 :]
                assert not dominates(_vec(nb), _vec(r))


def test_WE9_check_circuits_detects_cycle_and_runs_recursive_ll():
    """W-E9 (E10, Pseudocode 5): stale pairs make FIHC cycle
    (000 -> 100 -> 110 -> 010 -> 000) when x2 is missing from the VIG; with
    verification off, CheckCircuits must detect the return, find the bad
    step with real evaluations and add a dependency on x2."""
    from p3net.v005.elympus import fihc_elympus

    table = {
        (0, 0, 0): 2.0,
        (1, 0, 0): 1.0,
        (1, 1, 0): 3.0,
        (0, 1, 0): 0.0,
        (1, 0, 1): 3.0,
        (1, 1, 1): 1.0,
        (0, 0, 1): 0.0,
        (0, 1, 1): 2.0,
    }
    f1 = lambda x: table[vals(x)]  # noqa: E731
    f2 = lambda x: 0.0  # noqa: E731
    el1, el2 = _el([2, 2, 2]), _el([2, 2, 2])
    el1.vig.setdefault(0, set()).add(1)
    el1.vig.setdefault(1, set()).add(0)
    for x, var in [((0, 0, 0), 0), ((0, 1, 0), 0), ((1, 0, 1), 1), ((0, 0, 1), 1), ((1, 0, 0), 2)]:
        el1.partial_compare(G(*x), var, 1 - x[var], Counter(f1), False)
    for var in range(3):
        el2.partial_compare(G(0, 0, 0), var, 1, Counter(f2), False)
    ev = Counter(lambda x: (f1(x), f2(x)), cap=500)
    fihc_elympus(G(0, 0, 0), (el1, el2), ev, NeverVerify(), random.Random(0))
    assert any(2 in e for e in _edges(el1)), "cycle not resolved by a dependency on x2"


def test_WE10_separate_vig_per_objective():
    """W-E10 (E-2 a): f1 and f2 have separate eLyMPuS instances and VIGs."""
    el1, el2 = _el([K] * N), _el([K] * N)
    assert el1.vig is not el2.vig
    el1.vig.setdefault(0, set()).add(1)
    assert not el2.vig.get(0)


def test_WE10_real_evaluation_when_one_objective_has_no_pair():
    """W-E10 (E-2 a): a FIHC step needs a real evaluation if either
    objective lacks a pair -- with f2's lists empty, the same FIHC costs
    strictly more real evaluations than with both lists filled."""
    from p3net.v005.elympus import fihc_elympus

    el1, el2 = _el([K] * N), _el([K] * N)
    rng = random.Random(8)
    x = G(*(rng.randrange(K) for _ in range(N)))
    fihc_elympus(x, (el1, el2), Counter(_vec, cap=100_000), NeverVerify(), random.Random(1))
    both = Counter(_vec, cap=100_000)
    fihc_elympus(x, (copy.deepcopy(el1), copy.deepcopy(el2)), both, NeverVerify(), random.Random(1))
    only1 = Counter(_vec, cap=100_000)
    fihc_elympus(x, (copy.deepcopy(el1), _el([K] * N)), only1, NeverVerify(), random.Random(1))
    assert only1.n > both.n


def _p3e_run(budget=400, seed=0):
    from p3net.v005.elympus import P3ELyMPuS

    obj = CountingObjective(F1, F2)
    m = make(P3ELyMPuS, trap_space(NB, BS, K), budget, seed)
    return m, obj


def test_WE11_every_solution_in_pyramid_and_history_has_real_values():
    """W-E11 (E-3 a, O-5): every solution in the pyramid and in H_t was
    really evaluated (the FIHC-eLyMPuS result is evaluated before entering
    the pyramid)."""
    m, obj = _p3e_run()
    state = drive(m, obj, 400)
    evaluated = set(obj.calls)
    assert {vals(o.genotype) for o in state.history} == evaluated
    for lvl in m.pyramid.levels:
        for g in lvl:
            assert vals(g) in evaluated, "solution in the pyramid without a real evaluation"


@pytest.mark.parametrize("seed", range(4))
def test_WE12_always_verify_equals_plain_fihc(seed):
    """W-E12: with verification always on, FIHC-eLyMPuS follows the plain
    FIHC trajectory and reaches the same optimum (only the evaluation count
    differs); both get the same injected variable order (interfaces §7,
    Q-16)."""
    from p3net.v005.elympus import fihc_elympus
    from p3net.v005.p3.fihc import fihc

    rng = random.Random(100 + seed)
    x = G(*(rng.randrange(K) for _ in range(N)))

    def compare(a, b):
        fa, fb = _vec(vals(a)), _vec(vals(b))
        return 1 if dominates(fa, fb) else (-1 if dominates(fb, fa) else 0)

    order = list(range(N))
    random.Random(seed).shuffle(order)
    plain = fihc(x, compare, [K] * N, random.Random(seed), order=order)
    el = fihc_elympus(
        x,
        (_el([K] * N), _el([K] * N)),
        Counter(_vec, cap=100_000),
        AlwaysVerify(),
        random.Random(seed + 1),
        order=order,
    )
    assert vals(el) == vals(plain)


def test_WE13_memory_lives_for_the_whole_run():
    """W-E13: the VIGs and pair lists live for the whole run: the same
    eLyMPuS objects throughout, VIGs never shrink."""
    m, obj = _p3e_run(budget=600)
    from p3net.harness.runner import Observation, RunState

    state = RunState()
    first = None
    sizes = []
    while state.evaluations_used < 600:
        props = m.propose(state)
        if not props:
            break
        new = [Observation(genotype=g, objectives=obj(g)) for g in props]
        state.history.extend(new)
        state.evaluations_used += len(new)
        m.update(state, new)
        pair = tuple(m.elympus)
        if first is None:
            first = pair
        assert all(a is b for a, b in zip(pair, first)), "eLyMPuS memory was recreated"
        sizes.append(tuple(len(_edges(e)) for e in pair))
    assert all(all(b >= a for a, b in zip(s1, s2)) for s1, s2 in zip(sizes, sizes[1:]))


# --- Q-45: linkage of the P3-eLyMPuS pyramid (E-4, Z-E7 of 2026-10-21) ---
# Signatures (interfaces, supplement 2026-10-21, Q-46): `cluster_distance(table, ci, cj,
# known=None)`, `build_clusters(table, rng, known=None)` with
# known: Callable[[int, int], bool]; pair distance = entropy distance + 1 when
# not known(a, b); `p3net.v005.elympus.vig_known(elympus_pair)` builds
# `known` from the VIGs (Z-E7: known in either objective's VIG).

_ROWS_COPY = [(0, 0, 0), (0, 0, 1), (1, 1, 0), (1, 1, 1)]  # x1 == x0, x2 independent


def _table(domains, rows):
    from p3net.v005.p3.linkage import FrequencyTable

    t = FrequencyTable(list(domains))
    for r in rows:
        t.add(G(*r))
    return t


def test_E4_unknown_pair_distance_plus_one():
    """E-4 (OLyMPuS `Population::get_distance`): a variable pair the VIG does
    not know gets distance + 1; a known pair keeps the entropy distance (Eq.
    1). Hand values on x1 == x0, x2 independent: D(0,1) = 0, D(0,2) = 1."""
    from p3net.v005.p3.linkage import cluster_distance

    t = _table([2, 2, 2], _ROWS_COPY)
    known = lambda a, b: frozenset((a, b)) == frozenset((0, 1))  # noqa: E731
    assert math.isclose(cluster_distance(t, (0,), (1,), known=known), 0.0, abs_tol=1e-12)
    assert math.isclose(cluster_distance(t, (0,), (2,), known=known), 2.0)
    # cluster average over pairs: (0 + (1 + 1)) / 2
    assert math.isclose(cluster_distance(t, (0,), (1, 2), known=known), 1.0)
    # no penalty when everything is known; canonical P3 (known=None) unchanged
    assert math.isclose(cluster_distance(t, (0,), (2,), known=lambda a, b: True), 1.0)
    assert math.isclose(cluster_distance(t, (0,), (2,)), 1.0)


def test_E4_empty_vig_no_cluster_dropped_by_zero_distance_rule():
    """E-4: with an empty VIG every pair is unknown (distance >= 1), so the D = 0
    rule (P16) removes nothing -- {0} and {1} stay although x1 == x0; once the
    pair (0, 1) is known, the rule applies again and both go."""
    from p3net.v005.p3.linkage import build_clusters

    rng = random.Random(0)
    rows = []
    for _ in range(300):
        a = rng.randrange(3)
        rows.append((a, a, rng.randrange(3), rng.randrange(3)))
    t = _table([3] * 4, rows)
    unknown = [frozenset(c) for c in build_clusters(t, random.Random(0), known=lambda a, b: False)]
    assert frozenset({0}) in unknown and frozenset({1}) in unknown
    known01 = lambda a, b: frozenset((a, b)) == frozenset((0, 1))  # noqa: E731
    with_dep = [frozenset(c) for c in build_clusters(t, random.Random(0), known=known01)]
    assert frozenset({0}) not in with_dep and frozenset({1}) not in with_dep
    assert frozenset({0, 1}) in with_dep


def test_E4_known_if_in_either_objective_vig():
    """Z-E7: with two objectives a pair is known when the dependency is in the
    VIG of either eLyMPuS instance."""
    from p3net.v005.elympus import vig_known

    el1, el2 = _el([K] * N), _el([K] * N)
    el1.vig.setdefault(0, set()).add(1)
    el1.vig.setdefault(1, set()).add(0)
    el2.vig.setdefault(3, set()).add(5)
    el2.vig.setdefault(5, set()).add(3)
    known = vig_known((el1, el2))
    assert known(0, 1) and known(1, 0)
    assert known(3, 5) and known(5, 3)
    assert not known(0, 3) and not known(2, 4)


def test_E4_p3_elympus_pyramid_uses_vig_known():
    """E-4 / Z-E7 (interfaces supplement 2026-10-21: `Pyramid.known`, set by
    P3-eLyMPuS to `vig_known(self.elympus)`): the pyramid's `known` follows
    the VIGs of both eLyMPuS instances as they grow; canonical P3 has none."""
    from p3net.v005.elympus import P3ELyMPuS
    from p3net.v005.methods import P3Canonical

    m = make(P3ELyMPuS, trap_space(NB, BS, K), 200, 0)
    el1, el2 = m.elympus
    assert not m.pyramid.known(0, 1)
    el1.vig.setdefault(0, set()).add(1)
    el1.vig.setdefault(1, set()).add(0)
    el2.vig.setdefault(2, set()).add(7)
    el2.vig.setdefault(7, set()).add(2)
    assert m.pyramid.known(0, 1) and m.pyramid.known(1, 0) and m.pyramid.known(7, 2)
    assert not m.pyramid.known(0, 2)
    assert getattr(make(P3Canonical, trap_space(NB, BS, K), 200, 0).pyramid, "known", None) is None


def test_guard_trap_true_graph_is_blocks():
    """Helper guard: the ground-truth VIG used above is the block structure."""
    assert TRUE_EDGES == {
        frozenset(p)
        for b in range(NB)
        for p in itertools.combinations(range(b * BS, (b + 1) * BS), 2)
    }
