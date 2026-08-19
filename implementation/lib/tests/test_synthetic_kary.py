"""Tests for p3net.problem.synthetic_kary: k-ary trap-function validation
problem for eLyMPuS's k-ary generalisation (notes/plans/experiments-
przewozniczek-plan.md, Faza 2)."""

from __future__ import annotations

from p3net.problem.genotype import Genotype
from p3net.problem.synthetic_kary import (
    build_k_ary_trap_space,
    k_ary_trap_block,
    k_ary_trap_fitness,
    true_dependency_graph,
)


def test_block_trap_scores_global_optimum_highest():
    assert k_ary_trap_block((0, 0, 0, 0)) == 4.0


def test_block_trap_deceptive_local_optimum_is_second_best():
    # One variable off-target (u=3 of 4) scores worse than fully off-target
    # (u=0) -- the trap: a hill-climber drifting towards u=block_size gets
    # stuck one step short of the optimum.
    near_optimum = k_ary_trap_block((0, 0, 0, 1))
    fully_off = k_ary_trap_block((1, 1, 1, 1))
    assert near_optimum < fully_off
    assert near_optimum == 0.0
    assert fully_off == 3.0


def test_block_trap_is_deceptive_across_the_whole_unitation_range():
    scores = [k_ary_trap_block((0,) * u + (1,) * (4 - u)) for u in range(5)]
    assert scores == [3.0, 2.0, 1.0, 0.0, 4.0]


def test_search_space_has_expected_domain_size_and_length():
    space = build_k_ary_trap_space(n_blocks=2, block_size=4, alphabet_size=5)
    assert space.n == 8
    assert all(len(d.values) == 5 for d in space.domains)


def test_fitness_is_additive_and_minimisation_oriented():
    space = build_k_ary_trap_space(n_blocks=2, block_size=4, alphabet_size=4)
    optimum = Genotype(values=(0, 0, 0, 0, 0, 0, 0, 0))
    worst_deceptive = Genotype(values=(0, 0, 0, 1, 0, 0, 0, 1))
    assert k_ary_trap_fitness(optimum) < k_ary_trap_fitness(worst_deceptive)
    assert k_ary_trap_fitness(optimum) == -8.0


def test_true_dependency_graph_is_block_local_and_symmetric():
    graph = true_dependency_graph(n_blocks=2, block_size=4)
    assert graph[0] == {1, 2, 3}
    assert graph[4] == {5, 6, 7}
    for i, deps in graph.items():
        for j in deps:
            assert i in graph[j]
