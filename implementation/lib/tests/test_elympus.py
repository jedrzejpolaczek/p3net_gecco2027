"""Tests for p3net.surrogates.elympus: this project's own k-ary
generalisation of eLyMPuS (notes/plans/experiments-przewozniczek-plan.md,
Faza 2). Three checks mirrored from the plan: (1) correctness when the
empirical VIG equals the true VIG, (2) missing-dependency discovery
terminates and finds a real dependency, (3) measurable evaluation savings
versus full evaluation. Findings written up in
notes/lympus-nas-adaptation-validation.md."""

from __future__ import annotations

import math
import random

from p3net.problem.genotype import Genotype
from p3net.problem.synthetic_kary import (
    build_k_ary_trap_space,
    k_ary_trap_fitness,
    true_dependency_graph,
)
from p3net.surrogates.elympus import Comparison, ELyMPuS


def random_genotype(space, rng: random.Random) -> Genotype:
    return space.sample_uniform(rng)


def ground_truth_comparison(g: int, value, genotype: Genotype, fitness_fn) -> Comparison:
    current = fitness_fn(genotype)
    candidate = genotype.with_values(indices=[g], new_values=[value])
    return Comparison.of(fitness_fn(candidate), current)


# -- Check 1: correctness when eG = G ----------------------------------------


def test_partial_comparison_matches_ground_truth_when_dependencies_are_complete():
    space = build_k_ary_trap_space(n_blocks=3, block_size=4, alphabet_size=4)
    graph = true_dependency_graph(n_blocks=3, block_size=4)
    e = ELyMPuS(search_space=space, fitness_fn=k_ary_trap_fitness, dependencies=graph, rng=random.Random(0))

    rng = random.Random(0)
    for _ in range(200):
        genotype = random_genotype(space, rng)
        g = rng.randrange(space.n)
        domain = space.domains[g]
        value = rng.choice([v for v in domain.values if v != genotype.values[g]])
        expected = ground_truth_comparison(g, value, genotype, k_ary_trap_fitness)
        actual = e.partial_comparison(g, value, genotype)
        assert actual == expected


def test_partial_comparison_reuses_cache_across_different_genotypes_sharing_context():
    space = build_k_ary_trap_space(n_blocks=2, block_size=4, alphabet_size=4)
    graph = true_dependency_graph(n_blocks=2, block_size=4)
    e = ELyMPuS(search_space=space, fitness_fn=k_ary_trap_fitness, dependencies=graph, rng=random.Random(1))

    # g=1's dependencies are {0, 2, 3} (its own block) -- indices 4-7 (the
    # second block) are irrelevant to g=1 and safe to vary between a and b.
    a = Genotype(values=(0, 1, 2, 3, 0, 0, 0, 0))
    b = Genotype(values=(0, 1, 2, 3, 3, 3, 3, 3))

    e.partial_comparison(1, 0, a)
    count_after_first = e.evaluation_count
    e.partial_comparison(1, 0, b)
    assert e.evaluation_count == count_after_first


def test_rank_values_orders_better_before_tie_before_worse():
    space = build_k_ary_trap_space(n_blocks=1, block_size=4, alphabet_size=4)
    graph = true_dependency_graph(n_blocks=1, block_size=4)
    e = ELyMPuS(search_space=space, fitness_fn=k_ary_trap_fitness, dependencies=graph, rng=random.Random(2))

    genotype = Genotype(values=(0, 0, 0, 1))  # u=3 -> deceptive worst (score 0)
    ranked = e.rank_values(0, genotype)

    comparisons = [e.partial_comparison(0, v, genotype) for v in ranked]
    order = {Comparison.BETTER: 0, Comparison.TIE: 1, Comparison.WORSE: 2}
    assert comparisons == sorted(comparisons, key=lambda c: order[c])
    assert set(ranked) == {1, 2, 3}


# -- Check 2: missing-dependency discovery -----------------------------------


def test_discover_missing_dependency_finds_a_true_dependency_and_terminates():
    space = build_k_ary_trap_space(n_blocks=2, block_size=4, alphabet_size=4)
    # No known dependencies at all -- this is the incomplete-eG starting
    # point the source paper's RecursiveLL is meant to repair.
    e = ELyMPuS(search_space=space, fitness_fn=k_ary_trap_fitness, rng=random.Random(1))
    true_graph = true_dependency_graph(n_blocks=2, block_size=4)

    rng = random.Random(1)
    found = None
    attempts = 0
    while found is None and attempts < 200:
        attempts += 1
        x1 = random_genotype(space, rng)
        x2 = random_genotype(space, rng)
        g = rng.randrange(space.n)
        value = rng.choice([v for v in space.domains[g].values if v != x1.values[g]])
        if x1.values[g] != x2.values[g]:
            continue
        c1 = ground_truth_comparison(g, value, x1, k_ary_trap_fitness)
        c2 = ground_truth_comparison(g, value, x2, k_ary_trap_fitness)
        if c1 == c2:
            continue
        e.evaluation_count = 0
        found = e.discover_missing_dependency(g, value, x1, x2)
        if found is not None:
            n = space.n
            assert e.evaluation_count <= 2 * math.ceil(math.log2(n)) * 2
            assert found in true_graph[g]

    assert found is not None, "no mismatching (x1, x2, g, value) sampled in 200 attempts"


def test_partial_comparison_discovers_dependencies_at_runtime_when_verify_probability_is_set():
    """Regression test for the production wiring gap this fix closes:
    with `dependencies` starting empty (the real starting point
    `PrzewozniczekP3ELyMPuS` uses) and `verify_probability=1.0`,
    repeated `partial_comparison` calls across genuinely different
    genotypes sharing a (currently too-narrow) context must eventually
    grow `dependencies[g]` towards the true neighbourhood -- without
    this, `dependencies` stays permanently empty (see this class's
    module docstring and notes/lympus-nas-adaptation-validation.md)."""
    # n_blocks=2 (not 1): with a single block, every OTHER coordinate is a
    # true dependency, so a witness-tracking bug that attributes a
    # discovery to the wrong genotype could still only ever "discover" a
    # real edge -- it would never surface a FALSE cross-block edge the way
    # a multi-block problem does. This is exactly the false-positive
    # discovery a earlier, per-context (not per-cache-entry) witness
    # design produced in practice.
    space = build_k_ary_trap_space(n_blocks=2, block_size=4, alphabet_size=4)
    true_graph = true_dependency_graph(n_blocks=2, block_size=4)
    e = ELyMPuS(
        search_space=space,
        fitness_fn=k_ary_trap_fitness,
        verify_probability=1.0,
        rng=random.Random(3),
    )

    rng = random.Random(3)
    for _ in range(400):
        genotype = random_genotype(space, rng)
        g = rng.randrange(space.n)
        value = rng.choice([v for v in space.domains[g].values if v != genotype.values[g]])
        e.partial_comparison(g, value, genotype)

    assert any(e.dependencies[g] for g in range(space.n)), (
        "dependencies stayed empty after 400 partial_comparison calls with "
        "verify_probability=1.0 -- discovery is still not being triggered"
    )
    for g in range(space.n):
        assert e.dependencies[g] <= true_graph[g], (
            f"discovered a false dependency for g={g}: {e.dependencies[g]} not <= {true_graph[g]}"
        )


def test_discover_missing_dependency_returns_none_when_no_dependency_differs():
    space = build_k_ary_trap_space(n_blocks=1, block_size=4, alphabet_size=4)
    graph = true_dependency_graph(n_blocks=1, block_size=4)
    e = ELyMPuS(search_space=space, fitness_fn=k_ary_trap_fitness, dependencies=graph, rng=random.Random(3))
    x1 = Genotype(values=(0, 1, 2, 3))
    x2 = Genotype(values=(0, 1, 2, 3))
    assert e.discover_missing_dependency(0, 1, x1, x2) is None


# -- Check 3: FFE savings ------------------------------------------------------


def naive_hill_climb_evaluations(space, fitness_fn, start: Genotype, rng: random.Random) -> int:
    count = 0
    current = start
    current_fitness = fitness_fn(current)
    count += 1
    order = list(range(space.n))
    rng.shuffle(order)
    for i in order:
        alternatives = [v for v in space.domains[i].values if v != current.values[i]]
        rng.shuffle(alternatives)
        for value in alternatives:
            candidate = current.with_values(indices=[i], new_values=[value])
            candidate_fitness = fitness_fn(candidate)
            count += 1
            if candidate_fitness < current_fitness:
                current, current_fitness = candidate, candidate_fitness
                break
    return count


def elympus_hill_climb_evaluations(e: ELyMPuS, start: Genotype, rng: random.Random) -> int:
    """Same first-improvement policy and iteration order as
    `naive_hill_climb_evaluations` -- the only difference is routing each
    "is this alternative better than current" question through
    `partial_comparison` (context-cached, reusable across coordinates and
    across separate calls sharing the same `e`) instead of two fresh
    `fitness_fn` calls every time."""
    current = start
    order = list(range(e.search_space.n))
    rng.shuffle(order)
    for i in order:
        alternatives = [v for v in e.search_space.domains[i].values if v != current.values[i]]
        rng.shuffle(alternatives)
        for value in alternatives:
            if e.partial_comparison(i, value, current) == Comparison.BETTER:
                current = current.with_values(indices=[i], new_values=[value])
                break
    return e.evaluation_count


def test_elympus_guided_hill_climb_never_uses_more_evaluations_than_naive_on_a_cold_cache():
    """A single, cold-cache climb has little opportunity for reuse (see
    the module docstring: savings come from reusing comparisons ACROSS
    genotypes sharing context, e.g. across repeated FIHC calls within one
    P3 run -- checked by the next test). The only guarantee a single cold
    run gives is "never worse": partial_comparison never issues more than
    2 real evaluations per (g, context, value pair) queried, exactly what
    the naive climber issues per alternative tried."""
    space = build_k_ary_trap_space(n_blocks=4, block_size=4, alphabet_size=4)
    graph = true_dependency_graph(n_blocks=4, block_size=4)

    rng_naive = random.Random(42)
    start = random_genotype(space, rng_naive)
    naive_count = naive_hill_climb_evaluations(space, k_ary_trap_fitness, start, rng_naive)

    e = ELyMPuS(search_space=space, fitness_fn=k_ary_trap_fitness, dependencies=graph, rng=random.Random(4))
    rng_elympus = random.Random(42)
    start2 = random_genotype(space, rng_elympus)
    assert start2 == start
    elympus_count = elympus_hill_climb_evaluations(e, start2, rng_elympus)

    assert elympus_count <= naive_count


def test_elympus_saves_evaluations_across_repeated_runs_via_cache_reuse():
    """Table-4-style measurement: run several independent hill-climbs
    reusing the SAME ELyMPuS instance (so its cache persists, exactly as it
    would across P3-eLyMPuS's repeated FIHC calls within one search run)
    and compare total evaluations against the same number of independent
    naive climbs."""
    space = build_k_ary_trap_space(n_blocks=3, block_size=4, alphabet_size=4)
    graph = true_dependency_graph(n_blocks=3, block_size=4)

    rng_naive = random.Random(7)
    naive_total = 0
    for _ in range(15):
        start = random_genotype(space, rng_naive)
        naive_total += naive_hill_climb_evaluations(space, k_ary_trap_fitness, start, rng_naive)

    e = ELyMPuS(search_space=space, fitness_fn=k_ary_trap_fitness, dependencies=graph, rng=random.Random(5))
    rng_elympus = random.Random(7)
    for _ in range(15):
        start = random_genotype(space, rng_elympus)
        elympus_hill_climb_evaluations(e, start, rng_elympus)

    savings_fraction = 1.0 - (e.evaluation_count / naive_total)
    assert savings_fraction > 0.0
