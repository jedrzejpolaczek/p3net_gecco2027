"""Tests for p3net.problem.genotype -- generic SearchSpace/Genotype machinery."""

import random

import pytest

from p3net.problem.genotype import (
    CategoricalDomain,
    Genotype,
    SearchSpace,
    discretize_linear,
    discretize_log_uniform,
)


def make_toy_space() -> SearchSpace:
    """A small synthetic search space -- NOT the NAS one. Two categorical
    coordinates plus one pre-discretised "continuous" coordinate."""
    lr_grid = discretize_log_uniform(1e-4, 1e-1, 5)
    return SearchSpace(
        domains=(
            CategoricalDomain(values=("a", "b", "c")),
            CategoricalDomain(values=(0, 1)),
            CategoricalDomain(values=lr_grid),
        )
    )


def test_search_space_dimensionality():
    assert make_toy_space().n == 3


def test_sample_uniform_respects_domains():
    space = make_toy_space()
    rng = random.Random(0)
    for _ in range(50):
        genotype = space.sample_uniform(rng)
        assert space.contains(genotype)
        assert genotype.values[0] in ("a", "b", "c")
        assert genotype.values[1] in (0, 1)


def test_discretize_log_uniform_is_fixed_and_stable():
    grid_1 = discretize_log_uniform(1e-4, 1e-1, 5)
    grid_2 = discretize_log_uniform(1e-4, 1e-1, 5)
    assert grid_1 == grid_2
    assert len(grid_1) == 5
    assert grid_1[0] == pytest.approx(1e-4)
    assert grid_1[-1] == pytest.approx(1e-1)
    ratios = [grid_1[i + 1] / grid_1[i] for i in range(len(grid_1) - 1)]
    assert all(r == pytest.approx(ratios[0]) for r in ratios)


def test_discretize_linear_is_evenly_spaced():
    grid = discretize_linear(0.0, 1.0, 5)
    assert grid == pytest.approx((0.0, 0.25, 0.5, 0.75, 1.0))


def test_discretize_rejects_degenerate_grid():
    with pytest.raises(ValueError):
        discretize_linear(0.0, 1.0, 1)
    with pytest.raises(ValueError):
        discretize_log_uniform(0.0, 1.0, 5)


def test_genotype_equality_and_hash_for_cache_use():
    g1 = Genotype(values=("a", 0, 0.01))
    g2 = Genotype(values=("a", 0, 0.01))
    g3 = Genotype(values=("b", 0, 0.01))
    assert g1 == g2
    assert hash(g1) == hash(g2)
    assert g1 != g3
    cache = {g1: "first"}
    assert cache[g2] == "first"


def test_genotype_with_values_replaces_only_given_indices():
    g = Genotype(values=("a", 0, 0.01))
    g2 = g.with_values(indices=[1], new_values=[1])
    assert g2.values == ("a", 1, 0.01)
    assert g.values == ("a", 0, 0.01)


def test_categorical_domain_rejects_empty():
    with pytest.raises(ValueError):
        CategoricalDomain(values=())
