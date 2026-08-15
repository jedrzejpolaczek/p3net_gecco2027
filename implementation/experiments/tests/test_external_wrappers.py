"""Tests for methods.external.{mo_bohb,tpe} -- both real (Stage C):
mo_bohb_method wraps hpbandster's real BOHB config generator (Tchebycheff-
scalarised, see methods/external/mo_bohb.py's module docstring for why),
tpe_method wraps optuna's real TPESampler via its ask/tell API. (Gap in
the original task list -- adding it.)
"""

import random

import pytest
from p3net.harness.runner import Runner
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace

from methods.external.mo_bohb import mo_bohb_method
from methods.external.tpe import tpe_method


def toy_space() -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * 6)


def always_valid(genotype: Genotype) -> float:
    return -1.0


def rejects_all_zero(genotype: Genotype) -> float:
    """A real, non-trivial constraint: invalid iff every coordinate is 0."""
    return -1.0 if any(genotype.values) else 1.0


def toy_objective(genotype: Genotype):
    total = sum(genotype.values)
    return (float(total), float(len(genotype.values) - total))


@pytest.mark.parametrize("factory_name", ["tpe", "mo_bohb"])
def test_each_wrapper_runs_a_full_budget_without_error(factory_name):
    space = toy_space()
    if factory_name == "tpe":
        method = tpe_method(space, always_valid, seed=0)
    else:
        method = mo_bohb_method(space, always_valid, random.Random(0))
    state = Runner(objective=toy_objective, budget=15).run(method)
    assert state.evaluations_used == 15


@pytest.mark.parametrize("factory_name", ["tpe", "mo_bohb"])
def test_each_wrapper_respects_the_dedup_cache(factory_name):
    space = toy_space()
    if factory_name == "tpe":
        method = tpe_method(space, always_valid, seed=1)
    else:
        method = mo_bohb_method(space, always_valid, random.Random(1))
    state = Runner(objective=toy_objective, budget=15).run(method)
    seen = [obs.genotype for obs in state.history]
    assert len(seen) == len(set(seen))


@pytest.mark.parametrize("factory_name", ["tpe", "mo_bohb"])
def test_each_wrapper_never_proposes_an_invalid_genotype(factory_name):
    space = toy_space()
    if factory_name == "tpe":
        method = tpe_method(space, rejects_all_zero, seed=2)
    else:
        method = mo_bohb_method(space, rejects_all_zero, random.Random(2))
    state = Runner(objective=toy_objective, budget=15).run(method)
    for obs in state.history:
        assert any(obs.genotype.values), "an all-zero (invalid) genotype was proposed"


def test_experiment_type_is_distinct_per_baseline_for_cache_isolation():
    space = toy_space()
    assert tpe_method(space, always_valid, seed=3).experiment_type == "tpe"
    assert mo_bohb_method(space, always_valid, random.Random(3)).experiment_type == "mo_bohb"


def test_tpe_supports_more_than_two_objectives():
    space = toy_space()

    def three_objective(genotype: Genotype):
        total = sum(genotype.values)
        return (float(total), float(len(genotype.values) - total), float(total**2))

    method = tpe_method(space, always_valid, n_objectives=3, seed=4)
    state = Runner(objective=three_objective, budget=10).run(method)
    assert state.evaluations_used == 10
