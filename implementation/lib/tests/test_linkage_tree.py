"""Tests for p3net.search_engines.p3.linkage_tree."""

import random

import pytest

from p3net.problem.genotype import Genotype
from p3net.search_engines.p3.linkage_tree import build_linkage_tree, linkage_subsets


def make_dependent_population(n_samples: int, seed: int) -> list[Genotype]:
    """Variables 0 and 1 are perfectly correlated (a genuine dependency);
    variable 2 is independent noise. A correct linkage tree should group
    0 and 1 together before merging in 2."""
    rng = random.Random(seed)
    population = []
    for _ in range(n_samples):
        shared = rng.choice([0, 1])
        independent = rng.choice([0, 1])
        population.append(Genotype(values=(shared, shared, independent)))
    return population


def test_linkage_tree_groups_dependent_variables_first():
    population = make_dependent_population(200, seed=0)
    root = build_linkage_tree(population)
    subsets = linkage_subsets(root)
    assert frozenset({0, 1}) in subsets
    assert frozenset({0, 1, 2}) in subsets


def test_linkage_tree_root_covers_all_variables():
    population = make_dependent_population(50, seed=1)
    root = build_linkage_tree(population)
    assert root.subset == frozenset({0, 1, 2})


def test_linkage_tree_rejects_empty_population():
    with pytest.raises(ValueError):
        build_linkage_tree([])


def test_linkage_tree_rejects_mismatched_dimensionality():
    population = [Genotype(values=(0, 1)), Genotype(values=(0, 1, 2))]
    with pytest.raises(ValueError):
        build_linkage_tree(population)


def test_linkage_subsets_only_internal_nodes_not_leaves():
    population = make_dependent_population(50, seed=2)
    root = build_linkage_tree(population)
    subsets = linkage_subsets(root)
    for s in subsets:
        assert len(s) >= 2


def test_single_variable_genotype_yields_singleton_root():
    population = [Genotype(values=(0,)), Genotype(values=(1,)), Genotype(values=(0,))]
    root = build_linkage_tree(population)
    assert root.subset == frozenset({0})
    assert root.is_leaf
