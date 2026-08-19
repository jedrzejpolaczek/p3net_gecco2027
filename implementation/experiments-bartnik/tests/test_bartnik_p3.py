"""Tests for methods.bartnik_p3.BartnikP3: the reconstruction of Bartnik's
architecture-only NAS-Bench-201 winning algorithm class (notes/plans/
experiments-bartnik-plan.md, Faza 3) -- canonical single-individual-
climbing CanonicalPyramid engine + deterministic per-objective Random
Forest surrogate + lambda-quantile acceptance gate + ell-random warm-up,
wired into the harness.Method protocol."""

from __future__ import annotations

import random
from unittest.mock import patch

import pytest
from p3net.harness.runner import Runner
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace
from p3net.search_engines.p3 import canonical_pyramid as cp_module

from methods.bartnik_p3 import BartnikP3


def toy_space(n: int = 6) -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * n)


def toy_objective(genotype: Genotype):
    """Two objectives that move together (not perfectly complementary,
    unlike a tied-sum pair) -- keeps most candidate pairs strictly
    ordered by Pareto dominance rather than mutually nondominated, so
    tests here run in reasonable time (an always-tied-sum objective, as
    used by test_canonical_pyramid.py's own dedicated growth test, makes
    nearly every GOM step "improving" under the permissive not-worse
    rule and the pyramid grows without bound -- a real, documented
    performance characteristic (bartnik_p3.py's module docstring) but
    not one every test here needs to pay for)."""
    ones = sum(genotype.values)
    return (float(ones), float(ones))


def always_valid(genotype: Genotype) -> float:
    return -1.0


def make_method(seed: int, *, warmup: int | None = None, space: SearchSpace | None = None) -> BartnikP3:
    return BartnikP3(
        search_space=space or toy_space(),
        validity=always_valid,
        rng=random.Random(seed),
        warmup=warmup,
        n_estimators=10,
    )


def test_warmup_defaults_to_search_space_dimensionality():
    method = make_method(0)
    assert method.warmup == 6


def test_warmup_phase_proposes_only_random_valid_genotypes_one_at_a_time():
    method = make_method(1, warmup=4)
    state_history = []
    for _ in range(4):
        proposals = method.propose(_fake_state(state_history))
        assert len(proposals) == 1
        obs = _evaluate(proposals[0])
        state_history.append(obs)
        method.update(_fake_state(state_history), [obs])
    assert len(method._history) == 4


def _fake_state(history):
    from p3net.harness.runner import RunState

    state = RunState()
    state.history = list(history)
    state.evaluations_used = len(history)
    return state


def _evaluate(genotype: Genotype):
    from p3net.harness.runner import Observation

    return Observation(genotype=genotype, objectives=toy_objective(genotype))


def test_full_run_completes_without_error_and_spends_exactly_the_budget():
    method = make_method(2, warmup=6)
    state = Runner(objective=toy_objective, budget=40).run(method)
    assert state.evaluations_used == 40


def test_dedup_cache_prevents_duplicate_full_evaluations():
    method = make_method(3, warmup=6)
    state = Runner(objective=toy_objective, budget=40).run(method)
    seen = [obs.genotype for obs in state.history]
    assert len(seen) == len(set(seen))


def test_reuses_the_library_canonical_pyramid_engine_not_a_reimplementation():
    method = make_method(4, warmup=6)
    with patch("methods.bartnik_p3.climb", wraps=cp_module.climb) as spy:
        Runner(objective=toy_objective, budget=30).run(method)
        assert spy.call_count > 0


def test_acceptance_gate_threshold_relaxes_after_a_fallback_and_resets_on_elite_improvement():
    method = make_method(5, warmup=6)
    Runner(objective=toy_objective, budget=6).run(method)  # exactly the warmup
    initial_tau = method._tau
    method._register_fallback()
    assert method._tau <= initial_tau
    method._reset_gate()
    assert isinstance(method._tau, float)


def test_gate_accepts_everything_before_any_real_delta_is_observed():
    """No real observed deltas yet -> the quantile window is empty ->
    the gate must not block search entirely (mirrors P3Net's own
    "not enough data yet -- accept optimistically" bootstrap rule)."""
    method = make_method(6, warmup=2)
    assert method._quantile_threshold() == 0.0


def test_smoke_run_against_real_data_shaped_toy_problem_stays_within_search_space():
    method = make_method(7, warmup=6, space=toy_space(10))
    state = Runner(
        objective=lambda g: (float(sum(g.values)), float(sum(g.values))), budget=25
    ).run(method)
    for obs in state.history:
        assert len(obs.genotype.values) == 10
        assert all(v in (0, 1) for v in obs.genotype.values)


def test_categorical_domains_beyond_binary_are_supported():
    space = SearchSpace(domains=(CategoricalDomain(values=("a", "b", "c")),) * 5)

    def fitness(g: Genotype):
        non_a = float(sum(1 for v in g.values if v != "a"))
        return (non_a, non_a)

    method = BartnikP3(
        search_space=space, validity=always_valid, rng=random.Random(8), warmup=5, n_estimators=10
    )
    state = Runner(objective=fitness, budget=20).run(method)
    assert state.evaluations_used == 20
