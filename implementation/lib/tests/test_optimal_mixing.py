"""Tests for p3net.search_engines.p3.optimal_mixing."""

import random

from p3net.problem.genotype import Genotype
from p3net.search_engines.p3.linkage_tree import build_linkage_tree, linkage_subsets
from p3net.search_engines.p3.optimal_mixing import SweepState, propose_modification


def toy_population(seed: int) -> list[Genotype]:
    rng = random.Random(seed)
    return [Genotype(values=tuple(rng.choice([0, 1]) for _ in range(4))) for _ in range(30)]


def test_sweep_visits_every_current_subset_exactly_once():
    population = toy_population(0)
    root = build_linkage_tree(population)
    expected_subsets = set(linkage_subsets(root))

    parent = population[0]
    rng = random.Random(1)
    sweep = SweepState.start(parent, root, population, rng)
    visited = set()
    while not sweep.done:
        proposal = sweep.propose()
        visited.add(proposal.subset)
        sweep.reject(proposal)
    assert visited == expected_subsets


def test_proposal_modifies_only_the_visited_subset():
    parent = Genotype(values=(0, 0, 0, 0))
    donor = Genotype(values=(1, 1, 1, 1))
    subset = frozenset({1, 2})
    candidate = propose_modification(parent, donor, subset)
    assert candidate.values == (0, 1, 1, 0)


def test_accepted_step_carries_forward_to_next_proposal():
    population = toy_population(2)
    root = build_linkage_tree(population)
    parent = Genotype(values=(0, 0, 0, 0))
    rng = random.Random(3)
    sweep = SweepState.start(parent, root, population, rng)

    first = sweep.propose()
    sweep.accept(first)
    assert sweep.current == first.candidate

    second = sweep.propose()
    assert second.parent == first.candidate


def test_rejected_step_does_not_change_current_individual():
    population = toy_population(4)
    root = build_linkage_tree(population)
    parent = Genotype(values=(0, 0, 0, 0))
    rng = random.Random(5)
    sweep = SweepState.start(parent, root, population, rng)

    first = sweep.propose()
    sweep.reject(first)
    assert sweep.current == parent

    second = sweep.propose()
    assert second.parent == parent


def test_no_mutation_operator_exists_in_this_module():
    import p3net.search_engines.p3.optimal_mixing as om

    assert not hasattr(om, "mutate")
