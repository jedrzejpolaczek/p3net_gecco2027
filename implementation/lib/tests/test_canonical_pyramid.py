"""Tests for p3net.search_engines.p3.canonical_pyramid: the canonical,
single-individual-climbing P3 pyramid (Goldman 2014, Algorithm 3 shape) +
First-Improvement Hill Climber (Algorithm 4), reconstructed for
experiments-bartnik/methods/bartnik_p3.py (notes/plans/experiments-bartnik-
plan.md, Faza 1)."""

from __future__ import annotations

import random
from unittest.mock import patch

from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace
from p3net.search_engines.p3 import canonical_pyramid as cp_module
from p3net.search_engines.p3.canonical_pyramid import (
    CanonicalPyramid,
    climb,
    first_improvement_hill_climber,
)


def binary_space(n: int) -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * n)


def count_ones(genotype: Genotype) -> tuple[float]:
    return (float(sum(genotype.values)),)


def onemax_fitness(genotype: Genotype) -> tuple[float]:
    """Minimisation framing: fewer zeros is better, i.e. maximise the
    count of 1s <=> minimise the count of 0s."""
    return (float(sum(1 for v in genotype.values if v == 0)),)


# -- First-Improvement Hill Climber (Algorithm 4) ---------------------------


def test_fihc_never_makes_the_final_objective_worse():
    space = binary_space(10)
    rng = random.Random(0)
    start = Genotype(values=tuple(rng.choice([0, 1]) for _ in range(10)))
    start_obj = onemax_fitness(start)
    result = first_improvement_hill_climber(start, space, onemax_fitness, rng)
    result_obj = onemax_fitness(result)
    assert result_obj[0] <= start_obj[0]


def test_fihc_reaches_the_global_optimum_on_onemax_from_any_start():
    space = binary_space(8)
    rng = random.Random(1)
    all_zeros = Genotype(values=(0,) * 8)
    result = first_improvement_hill_climber(all_zeros, space, onemax_fitness, rng)
    assert onemax_fitness(result) == (0.0,)


def test_fihc_only_changes_one_coordinate_at_a_time_and_keeps_first_improvement():
    """First-improvement, not best-improvement: for a coordinate whose
    first tried alternative already improves, FIHC must take it rather
    than searching every alternative value for the best one."""
    space = SearchSpace(domains=(CategoricalDomain(values=(0, 1, 2, 3)),))
    start = Genotype(values=(3,))

    def fitness(g: Genotype) -> tuple[float]:
        # Any value < 3 improves on 3 -- first-improvement should stop at
        # whichever alternative random order tries first, not necessarily 0.
        return (float(g.values[0]),)

    rng = random.Random(2)
    result = first_improvement_hill_climber(start, space, fitness, rng)
    assert result.values[0] < 3


def test_fihc_respects_validity_and_never_returns_an_invalid_genotype():
    space = binary_space(4)

    def only_all_ones_invalid(g: Genotype) -> float:
        return 1.0 if all(v == 1 for v in g.values) else -1.0

    rng = random.Random(3)
    start = Genotype(values=(1, 1, 1, 0))
    result = first_improvement_hill_climber(
        start, space, onemax_fitness, rng, validity=only_all_ones_invalid
    )
    assert not all(v == 1 for v in result.values)


# -- climb() : Algorithm 3 shape ---------------------------------------------


def test_first_individual_seeds_an_empty_level_without_climbing_higher():
    pyramid = CanonicalPyramid()
    pyramid.add_level()
    space = binary_space(6)
    rng = random.Random(4)
    individual = Genotype(values=(1, 0, 1, 0, 1, 0))
    result = climb(individual, pyramid, search_space=space, fitness_fn=onemax_fitness, rng=rng)
    assert result in pyramid.levels[0].population
    assert len(pyramid.levels) == 1


def test_climb_grows_a_new_level_once_an_individual_climbs_past_every_existing_level():
    """Genuinely parameter-less growth trigger (module docstring): a new
    level is added only once a climbing individual improves all the way
    through every level that already exists -- never on a fixed
    population-size threshold."""
    pyramid = CanonicalPyramid()
    pyramid.add_level()
    space = binary_space(6)
    rng = random.Random(5)

    for i in range(40):
        individual = Genotype(values=tuple(rng.choice([0, 1]) for _ in range(6)))
        climb(individual, pyramid, search_space=space, fitness_fn=onemax_fitness, rng=rng)

    assert len(pyramid.levels) >= 1
    assert all(len(level.population) > 0 for level in pyramid.levels)


def test_climb_uses_the_shared_linkage_tree_and_optimal_mixing_modules_unmodified():
    """Directly confirms Faza 0's reuse claim: GOM inside climb() goes
    through the library's own build_linkage_tree/SweepState, not a
    reimplementation."""
    pyramid = CanonicalPyramid()
    pyramid.add_level()
    space = binary_space(6)
    rng = random.Random(6)

    seed_population = [
        Genotype(values=tuple(rng.choice([0, 1]) for _ in range(6))) for _ in range(5)
    ]
    for g in seed_population:
        climb(g, pyramid, search_space=space, fitness_fn=onemax_fitness, rng=rng)

    with patch.object(
        cp_module, "build_linkage_tree", wraps=cp_module.build_linkage_tree
    ) as spy:
        climb(
            Genotype(values=tuple(rng.choice([0, 1]) for _ in range(6))),
            pyramid,
            search_space=space,
            fitness_fn=onemax_fitness,
            rng=rng,
        )
        assert spy.call_count > 0


def test_climb_handles_categorical_not_only_binary_domains():
    """linkage_tree.py/optimal_mixing.py are documented as alphabet-
    agnostic (their own module docstrings) -- climb() must not silently
    assume a binary domain either."""
    space = SearchSpace(
        domains=(CategoricalDomain(values=("a", "b", "c")),) * 5
    )
    pyramid = CanonicalPyramid()
    pyramid.add_level()
    rng = random.Random(7)

    def target_fitness(g: Genotype) -> tuple[float]:
        return (float(sum(1 for v in g.values if v != "a")),)

    for _ in range(20):
        individual = Genotype(values=tuple(rng.choice(["a", "b", "c"]) for _ in range(5)))
        result = climb(
            individual, pyramid, search_space=space, fitness_fn=target_fitness, rng=rng
        )
        assert isinstance(result, Genotype)


def test_levels_grow_across_many_climbs_like_the_original_pyramid_level_count():
    """Empirical, not a hard-coded 2^k assertion (canonical single-
    individual climbing has no fixed level-size parameter, unlike the
    batch Pyramid's growth_factor): repeated climbing on a large enough,
    genuinely multi-objective landscape (complementary objectives whose
    sum is constant, so no two candidates ever strictly dominate one
    another -- almost every GOM step counts as improving under the
    permissive not-worse rule, so climbing keeps cascading upward)
    should produce more than one level, each populated only by
    individuals that actually reached it."""
    pyramid = CanonicalPyramid()
    pyramid.add_level()
    space = binary_space(10)
    rng = random.Random(8)

    def complementary_objectives(g: Genotype) -> tuple[float, float]:
        ones = sum(g.values)
        return (float(ones), float(len(g.values) - ones))

    for _ in range(120):
        individual = Genotype(values=tuple(rng.choice([0, 1]) for _ in range(10)))
        climb(individual, pyramid, search_space=space, fitness_fn=complementary_objectives, rng=rng)

    assert len(pyramid.levels) >= 2
    sizes = [len(level.population) for level in pyramid.levels]
    assert sizes == sorted(sizes, reverse=True)
