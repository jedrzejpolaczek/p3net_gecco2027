"""Level-1 tests for multi-objective regularized (aging) evolution (card
`notes/plans/v005-sources/regevo.md`, W-RE1-W-RE6).

Sources: Real et al., Regularized Evolution, AAAI 2019, Alg. 1; NAS-Bench-201
`R_EA.py`. Our adaptation (decision #24, RE-1 b): tournament winner by
NSGA-II crowded comparison computed on the whole population. O-RE2 (P = 20,
S = 5), O-RE3 (mutation: one variable to another value), O-RE4 (duplicate
child: no budget, enters the population).
"""

from __future__ import annotations

import importlib
import random
import sys
from collections import Counter as Multiset
from pathlib import Path

import pytest

from p3net.harness.runner import Observation

from ._support import (
    CountingObjective,
    G,
    additive_cost,
    assert_budget_respected,
    drive,
    drive_batches,
    hamming,
    make,
    random_weights,
    space_of,
    vals,
)


def _m():
    from p3net.v005.baselines import regevo

    return regevo


def _obj(domains, seed=0):
    w1 = random_weights(domains, seed)
    w2 = [[1.0 - x for x in row] for row in w1]
    return CountingObjective(additive_cost(w1), additive_cost(w2))


def _o(g, f):
    return Observation(genotype=G(*g), objectives=f)


def test_WRE3_rank_is_computed_on_the_population_not_the_sample():
    """W-RE3 (RE-1 b): B and C are mutually non-dominated in the sample, but
    B is dominated in the population (by D, not sampled) -> C (population
    rank 0) wins every time."""
    B, C, D = _o((0,), (2.0, 2.0)), _o((1,), (3.0, 1.0)), _o((2,), (1.0, 1.5))
    E = _o((3,), (5.0, 5.0))
    pop = [B, C, D, E]
    for s in range(20):
        random.seed(s)
        w = _m().crowded_winner([B, C, B], pop)
        assert vals(w) == vals(C)


def test_WRE3_crowding_tie_break_on_population_front():
    """W-RE3 (RE-1 b): equal population rank -> larger crowding distance in
    the population front wins (sample-local crowding would be infinite for
    both)."""
    P = [
        _o((i,), f)
        for i, f in enumerate([(0.0, 10.0), (1.0, 6.0), (2.0, 5.0), (6.0, 1.0), (10.0, 0.0)])
    ]
    # crowding on the population front: (1,6) and (2,5) are crowded, (6,1) is not
    for s in range(20):
        random.seed(s)
        assert vals(_m().crowded_winner([P[2], P[3]], P)) == vals(P[3])
        assert vals(_m().crowded_winner([P[1], P[3]], P)) == vals(P[3])


def test_WRE1_start_is_20_random_valid_evaluated():
    """W-RE1 (O-RE2): the first batch is P = 20 random, valid, distinct
    genotypes, all really evaluated."""
    from p3net.v005.common import is_valid

    space = space_of([4] * 8)
    batches = drive_batches(make(_m().RegEvo, space, 60, 0), _obj([4] * 8), 60)
    assert len(batches[0]) == 20 and len(set(batches[0])) == 20
    assert all(is_valid(space, G(*g)) for g in batches[0])
    assert all(len(b) == 1 for b in batches[1:])


def _spy_tournaments(monkeypatch):
    calls = []
    orig = _m().crowded_winner

    def spy(sample, population):
        calls.append(([vals(x) for x in sample], [vals(x) for x in population]))
        return orig(sample, population)

    monkeypatch.setattr(_m(), "crowded_winner", spy)
    return calls


def test_WRE2_sample_of_five_with_replacement(monkeypatch):
    """W-RE2 (O-RE2, Alg. 1: S random members with replacement): every
    tournament sample has S = 5 members drawn from the population, and
    repeats occur (P(repeat in 5 of 20) = 0.58 per tournament)."""
    calls = _spy_tournaments(monkeypatch)
    drive(make(_m().RegEvo, space_of([4] * 8), 60, 1), _obj([4] * 8), 60)
    assert len(calls) >= 30
    for sample, pop in calls:
        assert len(sample) == 5
        assert all(s in pop for s in sample)
    assert any(len(set(s)) < 5 for s, _ in calls), "sampling is without replacement"


def test_WRE4_mutation_changes_exactly_one_variable():
    """W-RE4 (O-RE3): every child differs from some population member in
    exactly one variable (never 0: no identity mutation)."""
    batches = drive_batches(make(_m().RegEvo, space_of([3] * 9), 80, 2), _obj([3] * 9), 80)
    seen = list(batches[0])
    for b in batches[1:]:
        child = b[0]
        assert any(hamming(child, p) == 1 for p in seen), f"{child} is not a 1-variable mutant"
        seen.append(child)


def test_WRE5_oldest_removed_population_constant(monkeypatch):
    """W-RE5 (Alg. 1 aging): after each child the oldest member is removed
    (FIFO); the population size stays 20. Population snapshots are read from
    the tournament calls."""
    calls = _spy_tournaments(monkeypatch)
    batches = drive_batches(make(_m().RegEvo, space_of([3] * 6), 80, 3), _obj([3] * 6), 80)
    queue = list(batches[0])
    pops = [Multiset(p) for _, p in calls]
    assert all(sum(p.values()) == 20 for p in pops)
    assert pops[0] == Multiset(queue)
    for before, after in zip(pops, pops[1:]):
        added = list((after - before).elements())
        removed = list((before - after).elements())
        if not added and not removed:  # child equal to the oldest
            queue = queue[1:] + queue[:1]
            continue
        assert len(added) == 1 and len(removed) == 1
        assert removed[0] == queue[0], "removed member is not the oldest"
        queue = queue[1:] + added


def test_WRE6_duplicate_child_enters_population_without_budget(monkeypatch):
    """W-RE6 (O-RE4): on a small space (2^5) duplicate children occur; they
    consume no budget but do enter the population (more children than
    evaluations)."""
    calls = _spy_tournaments(monkeypatch)
    obj = _obj([2] * 5)
    drive(make(_m().RegEvo, space_of([2] * 5), 30, 0), obj, 30)
    assert len(set(obj.calls)) == len(obj.calls)
    children_entered = len(calls) - 1
    assert children_entered > obj.n - 20, "duplicate children did not enter the population"


# --- Q-44: mutation unit choice (O-RE3 of 2026-10-20, Z-RE1; `R_EA.py`) ---

EXP = Path(__file__).resolve().parents[5] / "implementation" / "experiments"


def _exp_space(module, fn):
    if str(EXP) not in sys.path:
        sys.path.insert(0, str(EXP))
    try:
        mod = importlib.import_module(module)
    except ImportError as e:
        pytest.skip(f"cannot import {module}: {e}")
    return mod, getattr(mod, fn)()


def _mutations(monkeypatch, space, budget, seed, none_idx):
    """(parent, child) pairs read from tournament calls: parent = winner of
    tournament t, child = the member that entered the population before
    tournament t + 1. Pairs whose parent has a 'none' cell edge are dropped,
    so every single-edge change of the parent is a valid cell (no rejection
    can bias the distribution)."""
    calls = []
    orig = _m().crowded_winner

    def spy(sample, population):
        w = orig(sample, population)
        calls.append(([vals(x) for x in population], vals(w)))
        return w

    monkeypatch.setattr(_m(), "crowded_winner", spy)
    rng = random.Random(seed)
    w = [[rng.random() for _ in d.values] for d in space.domains]

    def f1(g):
        g = vals(g)
        return (
            1.0
            + 10.0 * sum(g[i] == none_idx[i] for i in none_idx)
            + sum(w[i][v] for i, v in enumerate(g))
        )

    def f2(g):
        g = vals(g)
        return 1.0 + sum(1.0 - w[i][v] for i, v in enumerate(g))

    drive(make(_m().RegEvo, space, budget, seed), CountingObjective(f1, f2), budget)
    pairs = []
    for (pop0, parent), (pop1, _) in zip(calls, calls[1:]):
        added = list((Multiset(pop1) - Multiset(pop0)).elements())
        if len(added) != 1:
            continue
        child = added[0]
        if any(parent[i] == none_idx[i] for i in none_idx):
            continue
        d = [i for i, (a, b) in enumerate(zip(parent, child)) if a != b]
        assert len(d) == 1, f"child differs from its parent in {d}"
        pairs.append(d[0])
    return pairs


def _chi2_ok(counts, probs):
    from scipy.stats import chisquare

    n = sum(counts)
    return chisquare(counts, [p * n for p in probs]).pvalue


def test_WRE4_cell_mutation_node_then_incoming_edge_nb201(monkeypatch):
    """W-RE4 (O-RE3 of 2026-10-20, `R_EA.py`): on NB201 the mutated edge is
    chosen as node j in {1, 2, 3} uniformly, then one of its j incoming edges
    uniformly: P(edge into node j) = 1/(3 j), i.e. 1/3, 1/6, 1/6, 1/9, 1/9,
    1/9. Coordinate -> node mapping read from `genotype_to_arch_str`.
    Chi-square p > 0.001 on >= 900 mutations; the uniform alternative is
    rejected."""
    mod, space = _exp_space("search_spaces.nas_bench_201_genotype", "nas_bench_201_search_space")
    ops = list(space.domains[0].values)
    none = ops.index("none")
    arch = mod.genotype_to_arch_str(tuple(f"{ops[1 + (i % 4)]}" for i in range(6)))
    node_of = [j + 1 for j, seg in enumerate(arch.split("+")) for _ in seg.strip("|").split("|")]
    assert len(node_of) == 6
    pairs = _mutations(monkeypatch, space, 1300, 0, {i: none for i in range(6)})
    assert len(pairs) >= 900, len(pairs)
    counts = [pairs.count(i) for i in range(6)]
    probs = [1 / (3 * node_of[i]) for i in range(6)]
    assert _chi2_ok(counts, probs) > 1e-3, (counts, probs)
    assert _chi2_ok(counts, [1 / 6] * 6) < 1e-3, "edge choice looks uniform"


def test_WRE4_hp_variables_are_units_on_par_with_nodes_jahs(monkeypatch):
    """W-RE4 (Z-RE1): on JAHS every non-cell variable is its own unit, drawn
    on par with the 3 nodes: each of the 4 HP variables 1/7, the cell edges
    together 3/7."""
    _, space = _exp_space("search_spaces.nas_genotype", "nas_search_space")
    none = list(space.domains[0].values).index("none")
    pairs = _mutations(monkeypatch, space, 1300, 1, {i: none for i in range(6)})
    assert len(pairs) >= 900, len(pairs)
    n_hp = len(space.domains) - 6
    counts = [sum(p < 6 for p in pairs)] + [pairs.count(6 + i) for i in range(n_hp)]
    units = 3 + n_hp
    probs = [3 / units] + [1 / units] * n_hp
    assert _chi2_ok(counts, probs) > 1e-3, (counts, probs)


def test_WRE4_uniform_variable_choice_without_cell(monkeypatch):
    """W-RE4 (O-RE3): in a space without a cell the mutated variable is
    uniform over variables."""
    space = space_of([4] * 6)
    pairs = _mutations(monkeypatch, space, 1300, 2, {})
    assert len(pairs) >= 900, len(pairs)
    assert _chi2_ok([pairs.count(i) for i in range(6)], [1 / 6] * 6) > 1e-3


@pytest.mark.parametrize("budget", [20, 21, 57])
def test_WRE6_budget_never_exceeded(budget):
    """W-RE6 (K-2): exactly b real evaluations."""
    obj = _obj([4] * 8)
    drive(make(_m().RegEvo, space_of([4] * 8), budget, 5), obj, budget)
    assert_budget_respected(obj, budget, exact=True)
