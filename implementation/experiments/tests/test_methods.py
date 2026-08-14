"""Tests for baseline methods, all run against the same synthetic
substrate. (Gap in the original task list -- adding it.)"""

import random
from unittest.mock import patch

import pytest
from p3net.harness.runner import Runner
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace
from p3net.search_engines.p3.linkage_tree import build_linkage_tree as real_build_linkage_tree
from sklearn.linear_model import LinearRegression

from methods.nsga_net import NSGANet
from methods.nsganetv2 import NSGANetV2
from methods.p3_absolute import P3Absolute
from methods.p3_alone import P3Alone
from methods.random_search import RandomSearch


def toy_space() -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * 8)


def toy_objective(genotype: Genotype):
    return (float(sum(genotype.values)),)


def always_valid(genotype: Genotype) -> float:
    return -1.0


def _make_methods(seed: int, space: SearchSpace) -> dict:
    return {
        "nsga_net": NSGANet(
            search_space=space, validity=always_valid, rng=random.Random(seed), population_size=10
        ),
        "nsganetv2": NSGANetV2(
            search_space=space,
            validity=always_valid,
            model_factory=LinearRegression,
            rng=random.Random(seed),
            population_size=10,
        ),
        "p3_alone": P3Alone(
            search_space=space, validity=always_valid, rng=random.Random(seed), population_size=10
        ),
        "p3_absolute": P3Absolute(
            search_space=space,
            validity=always_valid,
            model_factory=LinearRegression,
            rng=random.Random(seed),
            population_size=10,
        ),
        "random_search": RandomSearch(
            search_space=space, validity=always_valid, rng=random.Random(seed)
        ),
    }


@pytest.mark.parametrize(
    "name", ["nsga_net", "nsganetv2", "p3_alone", "p3_absolute", "random_search"]
)
def test_each_arm_runs_a_full_budget_without_error(name):
    space = toy_space()
    method = _make_methods(0, space)[name]
    state = Runner(objective=toy_objective, budget=40).run(method)
    assert state.evaluations_used == 40


@pytest.mark.parametrize(
    "name", ["nsga_net", "nsganetv2", "p3_alone", "p3_absolute", "random_search"]
)
def test_dedup_cache_prevents_duplicate_full_evaluations(name):
    space = toy_space()
    method = _make_methods(1, space)[name]
    state = Runner(objective=toy_objective, budget=40).run(method)
    seen = [obs.genotype for obs in state.history]
    assert len(seen) == len(set(seen))


def test_p3_alone_reuses_the_library_p3_engine_not_a_reimplementation():
    space = toy_space()
    method = P3Alone(
        search_space=space, validity=always_valid, rng=random.Random(2), population_size=8
    )
    with patch("methods.p3_alone.build_linkage_tree", wraps=real_build_linkage_tree) as spy:
        Runner(objective=toy_objective, budget=30).run(method)
        assert spy.call_count > 0


def test_p3_absolute_reuses_the_library_p3_engine_not_a_reimplementation():
    space = toy_space()
    method = P3Absolute(
        search_space=space,
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(3),
        population_size=8,
    )
    with patch("methods.p3_absolute.build_linkage_tree", wraps=real_build_linkage_tree) as spy:
        Runner(objective=toy_objective, budget=30).run(method)
        assert spy.call_count > 0


def test_p3_alone_tracks_sweeps_completed_diagnostic():
    space = toy_space()
    method = P3Alone(
        search_space=space, validity=always_valid, rng=random.Random(4), population_size=8
    )
    Runner(objective=toy_objective, budget=30).run(method)
    assert method.sweeps_completed >= 1


def test_random_search_has_no_population_state_unlike_every_other_arm():
    method = RandomSearch(search_space=toy_space(), validity=always_valid, rng=random.Random(5))
    assert not hasattr(method, "_population")
