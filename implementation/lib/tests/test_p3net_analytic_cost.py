"""Tests for p3net.methods.p3net.P3Net's optional analytic_cost hook --
lets step 4's C* selection freshly compute non-f1 objectives per
candidate instead of inheriting the ancestor's value (module docstring's
"Known simplification 2", resolved for callers who supply analytic_cost;
the previous approximation remains the documented default when they
don't). (Gap in the original task list -- adding it.)
"""

import random
from unittest.mock import MagicMock

import pytest
from sklearn.linear_model import LinearRegression

from p3net.harness.runner import Observation, Runner
from p3net.methods.p3net import P3Net
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace
from p3net.surrogates.relative_linkage_aware import RelativeLinkageAwareSurrogate
from p3net.surrogates.telescoping import ChainStep


def toy_space(n: int) -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * n)


def always_valid(genotype: Genotype) -> float:
    return -1.0


def _fitted_surrogate_and_observations():
    data = [
        (Genotype(values=("a", 0)), (10.0, 100.0)),
        (Genotype(values=("b", 0)), (20.0, 200.0)),
        (Genotype(values=("a", 1)), (10.0, 100.0)),
        (Genotype(values=("b", 1)), (20.0, 200.0)),
    ]
    observations = [Observation(genotype=g, objectives=o) for g, o in data]
    surrogate = RelativeLinkageAwareSurrogate(model_factory=LinearRegression)
    surrogate.fit(observations, subsets=[frozenset({0})])
    return surrogate, observations


def test_analytic_cost_defaults_to_none_and_existing_behaviour_is_unchanged():
    space = toy_space(6)
    method = P3Net(
        search_space=space,
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
    )
    assert method.analytic_cost is None
    state = Runner(objective=lambda g: (float(sum(g.values)),), budget=30).run(method)
    assert state.evaluations_used == 30


def test_analytic_cost_is_used_for_non_f1_objectives_in_tentative_accept():
    """Direct test of _tentatively_accept (same fabricated-surrogate
    pattern as tests/test_telescoping.py) -- the returned estimate's
    non-f1 entry must come from analytic_cost(candidate), not the
    ancestor's f2."""
    surrogate, observations = _fitted_surrogate_and_observations()
    ancestor = observations[0]  # ("a", 0), f1=10.0, f2=100.0
    candidate = Genotype(values=("b", 0))
    chain = [ChainStep(x_prev=ancestor.genotype, x_next=candidate, subset=frozenset({0}))]

    method = P3Net(
        search_space=toy_space(2),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
        analytic_cost=lambda g: (0.0, 999.0),
    )
    method._history = {obs.genotype: obs for obs in observations}

    _accept, estimated = method._tentatively_accept(surrogate, ancestor, chain, candidate)
    assert estimated[1] == pytest.approx(999.0)
    assert estimated[1] != pytest.approx(ancestor.objectives[1])


def test_analytic_cost_none_falls_back_to_inheriting_the_ancestors_value():
    """Same setup, but without analytic_cost -- must reproduce the
    documented pre-existing simplification exactly, proving the fallback
    for callers who don't supply the hook is unchanged."""
    surrogate, observations = _fitted_surrogate_and_observations()
    ancestor = observations[0]
    candidate = Genotype(values=("b", 0))
    chain = [ChainStep(x_prev=ancestor.genotype, x_next=candidate, subset=frozenset({0}))]

    method = P3Net(
        search_space=toy_space(2),
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(0),
    )
    method._history = {obs.genotype: obs for obs in observations}

    _accept, estimated = method._tentatively_accept(surrogate, ancestor, chain, candidate)
    assert estimated[1] == pytest.approx(ancestor.objectives[1])


def test_analytic_cost_is_invoked_with_genotypes_during_a_real_sweep():
    """Black-box confirmation the hook is wired into the hot path, not
    just accepted and ignored: spy on analytic_cost and confirm it's
    actually called once the population is large enough to sweep."""

    def real_cost(g: Genotype):
        return (0.0, float(sum(g.values)))

    spy = MagicMock(side_effect=real_cost)
    space = toy_space(6)
    method = P3Net(
        search_space=space,
        validity=always_valid,
        model_factory=LinearRegression,
        rng=random.Random(2),
        analytic_cost=spy,
    )
    Runner(objective=lambda g: (float(sum(g.values)), 0.0), budget=30).run(method)
    assert spy.call_count > 0
    for call in spy.call_args_list:
        assert isinstance(call.args[0], Genotype)
