"""Tests for P3Net's population-pyramid wiring (module docstring's
"Known simplification 1", now resolved: population size is no longer a
constructor argument -- level 0 starts at `growth_factor` individuals and
new, larger levels grow automatically once the current level's sweep
passes stop improving). (Gap in the original task list -- adding it.)
"""

import random

import pytest
from sklearn.linear_model import LinearRegression

from p3net.harness.runner import Runner
from p3net.methods.p3net import P3Net
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace


def toy_space(n: int = 12) -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * n)


def always_valid(genotype: Genotype) -> float:
    return -1.0


def toy_objective(genotype: Genotype):
    return (-float(sum(genotype.values)),)


def test_no_population_size_constructor_argument():
    """The whole point of this follow-up: population size must no longer
    be user-specified."""
    import dataclasses

    field_names = {f.name for f in dataclasses.fields(P3Net)}
    assert "population_size" not in field_names
    assert "growth_factor" in field_names


def test_level_0_starts_at_growth_factor_individuals():
    method = P3Net(
        search_space=toy_space(),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
        growth_factor=3,
    )
    assert len(method._pyramid.levels) == 1
    assert method._pyramid.levels[0].size == 3


def test_growth_factor_is_configurable_and_changes_level_sizes():
    method = P3Net(
        search_space=toy_space(),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
        growth_factor=4,
    )
    assert method._pyramid.levels[0].size == 4


def test_pyramid_grows_new_levels_over_a_longer_run():
    """Over a long enough run on a problem where the small level 0
    quickly exhausts easy improvements, at least one new, larger level
    must be grown -- proving growth is real, not just accepted and
    ignored."""
    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(3),
        growth_factor=2,
    )
    Runner(objective=toy_objective, budget=150).run(method)
    assert len(method._pyramid.levels) > 1
    sizes = [level.size for level in method._pyramid.levels]
    assert sizes == sorted(sizes)
    assert len(set(sizes)) == len(sizes)  # strictly growing, per Pyramid's own contract


def test_pyramid_growth_is_bounded_by_budget_not_runaway():
    """A finite budget must never be exceeded regardless of how many
    levels get grown."""
    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(4),
        growth_factor=2,
    )
    state = Runner(objective=toy_objective, budget=100).run(method)
    assert state.evaluations_used <= 100


def test_old_levels_history_is_preserved_in_h_t_after_growth():
    """Simplification 1 (module docstring): once a level stalls and a new
    one grows, the old level is frozen but its real evaluations must
    still be part of H_t (never discarded)."""
    method = P3Net(
        search_space=toy_space(10),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(5),
        growth_factor=2,
    )
    state = Runner(objective=toy_objective, budget=120).run(method)
    if len(method._pyramid.levels) > 1:
        old_level_genotypes = method._pyramid.levels[0].population
        for g in old_level_genotypes:
            assert g in method._history
    assert len(method._history) == len({obs.genotype for obs in state.history})


def test_best_objectives_seeded_after_bootstrap_before_any_promote_call():
    """_seed_best_objectives must run exactly once bootstrap completes,
    giving promote() a real baseline rather than leaving best_objectives
    None (which would make the first post-bootstrap pass always count as
    "improving" regardless of its actual quality)."""
    method = P3Net(
        search_space=toy_space(6),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(6),
        growth_factor=4,
    )
    level = method._pyramid.levels[0]
    Runner(objective=toy_objective, budget=4).run(method)
    assert len(level.population) == level.size
    assert level.best_objectives is not None


@pytest.mark.parametrize("growth_factor", [2, 3])
def test_p3net_still_outperforms_random_search_with_pyramid_wiring(growth_factor):
    """Regression guard: pyramid wiring must not make search worse on the
    same structured toy problem the pre-pyramid implementation was
    validated against (tests/test_p3net_integration.py)."""

    def trap_objective(genotype: Genotype):
        def trap4(u: int) -> int:
            return 4 if u == 4 else 3 - u

        total = sum(trap4(sum(genotype.values[b * 4 : (b + 1) * 4])) for b in range(3))
        return (-float(total),)

    space = toy_space(12)
    budget = 200
    method = P3Net(
        search_space=space,
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(42),
        growth_factor=growth_factor,
    )
    state = Runner(objective=trap_objective, budget=budget).run(method)
    p3net_best = min(obs.objectives[0] for obs in state.history)

    rng = random.Random(42)
    random_best = min(trap_objective(space.sample_uniform(rng))[0] for _ in range(budget))
    assert p3net_best <= random_best
