"""Tests for methods.external.{sh_emoa,mo_bohb,tpe} -- the ask/tell
adapter logic, with the underlying algorithm mocked/stubbed since those
packages aren't installed yet (Stage C). Asserts only the adapter logic:
genotype translation, budget/seed/dedup integration. (Gap in the original
task list -- adding it.)"""

import random

import pytest
from p3net.harness.runner import Runner
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace

from methods.external._ask_tell_shared import default_valid_sampler
from methods.external.mo_bohb import mo_bohb_method
from methods.external.sh_emoa import sh_emoa_method
from methods.external.tpe import tpe_method


def toy_space() -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * 6)


def always_valid(genotype: Genotype) -> float:
    return -1.0


def toy_objective(genotype: Genotype):
    return (float(sum(genotype.values)),)


@pytest.mark.parametrize("factory", [sh_emoa_method, mo_bohb_method, tpe_method])
def test_each_wrapper_runs_a_full_budget_with_a_stub_sampler(factory):
    space = toy_space()
    sampler = default_valid_sampler(space, always_valid, random.Random(0))
    method = factory(sampler)
    state = Runner(objective=toy_objective, budget=25).run(method)
    assert state.evaluations_used == 25


@pytest.mark.parametrize("factory", [sh_emoa_method, mo_bohb_method, tpe_method])
def test_each_wrapper_respects_the_dedup_cache(factory):
    space = toy_space()
    sampler = default_valid_sampler(space, always_valid, random.Random(1))
    method = factory(sampler)
    state = Runner(objective=toy_objective, budget=25).run(method)
    seen = [obs.genotype for obs in state.history]
    assert len(seen) == len(set(seen))


def test_report_callback_is_invoked_with_genotype_and_objectives():
    reported: list[tuple[Genotype, tuple]] = []

    def report(genotype: Genotype, objectives) -> None:
        reported.append((genotype, objectives))

    space = toy_space()
    sampler = default_valid_sampler(space, always_valid, random.Random(2))
    method = sh_emoa_method(sampler, report=report)
    Runner(objective=toy_objective, budget=10).run(method)
    assert len(reported) == 10
    for genotype, objectives in reported:
        assert objectives == toy_objective(genotype)


def test_report_is_optional():
    space = toy_space()
    sampler = default_valid_sampler(space, always_valid, random.Random(3))
    method = tpe_method(sampler)  # no report callback
    state = Runner(objective=toy_objective, budget=10).run(method)
    assert state.evaluations_used == 10


def test_experiment_type_is_distinct_per_baseline_for_cache_isolation():
    space = toy_space()
    sampler = default_valid_sampler(space, always_valid, random.Random(4))
    assert sh_emoa_method(sampler).experiment_type == "sh_emoa"
    assert mo_bohb_method(sampler).experiment_type == "mo_bohb"
    assert tpe_method(sampler).experiment_type == "tpe"
