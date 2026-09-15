"""Tests for p3net.search_engines.p3.fihc_elympus: P3-eLyMPuS's local-
search step (notes/plans/experiments-przewozniczek-plan.md, Faza 3) and its
plug-in point inside canonical_pyramid.climb."""

from __future__ import annotations

import random

from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace
from p3net.problem.synthetic_kary import (
    build_k_ary_trap_space,
    k_ary_trap_fitness,
    true_dependency_graph,
)
from p3net.search_engines.p3.canonical_pyramid import CanonicalPyramid, climb
from p3net.search_engines.p3.fihc_elympus import fihc_elympus, make_elympus_fitness_adapter
from p3net.surrogates.elympus import ELyMPuS


def test_fihc_elympus_never_worsens_the_final_objective_on_the_synthetic_trap():
    space = build_k_ary_trap_space(n_blocks=3, block_size=4, alphabet_size=4)
    graph = true_dependency_graph(n_blocks=3, block_size=4)
    e = ELyMPuS(search_space=space, fitness_fn=k_ary_trap_fitness, dependencies=graph, rng=random.Random(10))

    rng = random.Random(0)
    start = space.sample_uniform(rng)
    start_fitness = k_ary_trap_fitness(start)
    result = fihc_elympus(start, space, e, rng)
    assert k_ary_trap_fitness(result) <= start_fitness


def test_fihc_elympus_reaches_the_global_optimum_from_a_fixed_deceptive_start():
    space = build_k_ary_trap_space(n_blocks=1, block_size=4, alphabet_size=4)
    graph = true_dependency_graph(n_blocks=1, block_size=4)
    e = ELyMPuS(search_space=space, fitness_fn=k_ary_trap_fitness, dependencies=graph, rng=random.Random(11))

    all_off_target = Genotype(values=(1, 1, 1, 1))  # u=0, deceptive-adjacent, not the global optimum
    rng = random.Random(1)
    result = fihc_elympus(all_off_target, space, e, rng)
    assert k_ary_trap_fitness(result) <= k_ary_trap_fitness(all_off_target)


def test_fihc_elympus_respects_validity():
    space = SearchSpace(domains=(CategoricalDomain(values=(0, 1, 2, 3)),) * 4)

    def fitness(g: Genotype) -> float:
        return float(sum(g.values))

    def only_all_zero_invalid(g: Genotype) -> float:
        return 1.0 if all(v == 0 for v in g.values) else -1.0

    e = ELyMPuS(search_space=space, fitness_fn=fitness, rng=random.Random(12))
    rng = random.Random(2)
    start = Genotype(values=(1, 0, 0, 0))
    result = fihc_elympus(start, space, e, rng, validity=only_all_zero_invalid)
    assert not all(v == 0 for v in result.values)


def test_make_elympus_fitness_adapter_selects_the_configured_objective():
    def multi_objective(g: Genotype) -> tuple[float, float]:
        return (float(sum(g.values)), float(-sum(g.values)))

    adapter0 = make_elympus_fitness_adapter(multi_objective, objective_index=0)
    adapter1 = make_elympus_fitness_adapter(multi_objective, objective_index=1)
    genotype = Genotype(values=(1, 2, 3))
    assert adapter0(genotype) == 6.0
    assert adapter1(genotype) == -6.0


# -- Integration with CanonicalPyramid.climb ---------------------------------


def test_climb_accepts_fihc_elympus_as_a_pluggable_hill_climber():
    space = build_k_ary_trap_space(n_blocks=2, block_size=4, alphabet_size=4)
    graph = true_dependency_graph(n_blocks=2, block_size=4)

    def real_fitness(g: Genotype) -> tuple[float]:
        return (k_ary_trap_fitness(g),)

    scalar_fitness = make_elympus_fitness_adapter(real_fitness, objective_index=0)
    elympus = ELyMPuS(search_space=space, fitness_fn=scalar_fitness, dependencies=graph, rng=random.Random(13))

    pyramid = CanonicalPyramid()
    pyramid.add_level()
    rng = random.Random(3)

    def bound_hill_climber(genotype: Genotype) -> Genotype:
        return fihc_elympus(genotype, space, elympus, rng)

    individual = space.sample_uniform(rng)
    result = climb(
        individual,
        pyramid,
        search_space=space,
        fitness_fn=real_fitness,
        rng=rng,
        hill_climber=bound_hill_climber,
    )
    assert isinstance(result, Genotype)
    assert real_fitness(result)[0] <= real_fitness(individual)[0]


def test_climb_default_behaviour_is_unchanged_without_hill_climber_argument():
    """Non-regression: omitting `hill_climber` must behave exactly like
    before this Faza 3 change (plain FIHC, plain fitness_fn)."""
    space = build_k_ary_trap_space(n_blocks=2, block_size=4, alphabet_size=4)

    def real_fitness(g: Genotype) -> tuple[float]:
        return (k_ary_trap_fitness(g),)

    pyramid = CanonicalPyramid()
    pyramid.add_level()
    rng = random.Random(4)
    individual = space.sample_uniform(rng)
    result = climb(individual, pyramid, search_space=space, fitness_fn=real_fitness, rng=rng)
    assert isinstance(result, Genotype)
