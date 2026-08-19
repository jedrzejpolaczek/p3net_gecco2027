"""Tests for p3net.surrogates.relative_linkage_aware."""

import pytest
from sklearn.linear_model import LinearRegression

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype
from p3net.surrogates.relative_linkage_aware import (
    NoLinkageTreeError,
    RelativeLinkageAwareSurrogate,
)


def make_observations() -> list[Observation]:
    # f1 depends only on coordinate 0: "a" -> 10, "b" -> 20. Coordinate 1 is
    # a no-op decoy.
    data = [
        (Genotype(values=("a", 0)), (10.0,)),
        (Genotype(values=("b", 0)), (20.0,)),
        (Genotype(values=("a", 1)), (10.0,)),
        (Genotype(values=("b", 1)), (20.0,)),
    ]
    return [Observation(genotype=g, objectives=o) for g, o in data]


def test_trains_on_pairwise_diffs_restricted_to_subset():
    surrogate = RelativeLinkageAwareSurrogate(model_factory=LinearRegression)
    subset = frozenset({0})
    surrogate.fit(make_observations(), subsets=[subset])

    x = Genotype(values=("a", 0))
    x_prime = Genotype(values=("b", 0))
    predicted_delta = surrogate.predict(x, x_prime, subset)
    true_delta = 10.0 - 20.0
    assert predicted_delta == pytest.approx(true_delta, abs=2.0)


def test_raises_when_no_pair_differs_only_within_given_subsets():
    surrogate = RelativeLinkageAwareSurrogate(model_factory=LinearRegression)
    obs = [
        Observation(genotype=Genotype(values=("a", 0)), objectives=(10.0,)),
        Observation(genotype=Genotype(values=("b", 1)), objectives=(20.0,)),
    ]
    with pytest.raises(NoLinkageTreeError):
        surrogate.fit(obs, subsets=[frozenset({1})])


def test_predict_before_fit_raises_loudly():
    surrogate = RelativeLinkageAwareSurrogate(model_factory=LinearRegression)
    with pytest.raises(NoLinkageTreeError):
        surrogate.predict(Genotype(values=("a", 0)), Genotype(values=("b", 0)), frozenset({0}))


def test_predict_rejects_subset_not_seen_at_fit_time():
    surrogate = RelativeLinkageAwareSurrogate(model_factory=LinearRegression)
    surrogate.fit(make_observations(), subsets=[frozenset({0})])
    with pytest.raises(ValueError):
        surrogate.predict(Genotype(values=("a", 0)), Genotype(values=("a", 1)), frozenset({1}))


def test_include_interactions_defaults_to_false():
    """Default behaviour (2026-08-18, Phase 4 of the pyramid/surrogate fix
    plan) must be unchanged -- interaction columns are opt-in, matching
    every other single-axis ablation this project has added
    (p3net.py module docstring's "Known simplifications" list)."""
    assert RelativeLinkageAwareSurrogate(model_factory=LinearRegression).include_interactions is False


def _and_pattern_observations() -> list[Observation]:
    # f1 is 10 only when BOTH coordinates are 1, 0 otherwise -- not
    # decomposable as g(coord0) + h(coord1) for any g, h: every single-
    # coordinate flip leaves f1 at 0, but flipping both at once jumps it
    # to 10. A purely additive model (Results, "Diagnostics: surrogate
    # representational capacity") cannot represent this; a model with a
    # "did both coordinates change together" interaction term can.
    data = [
        (Genotype(values=(0, 0)), (0.0,)),
        (Genotype(values=(1, 0)), (0.0,)),
        (Genotype(values=(0, 1)), (0.0,)),
        (Genotype(values=(1, 1)), (10.0,)),
    ]
    return [Observation(genotype=g, objectives=o) for g, o in data]


def test_include_interactions_lets_the_model_represent_a_non_additive_pattern():
    subset = frozenset({0, 1})
    observations = _and_pattern_observations()

    additive_only = RelativeLinkageAwareSurrogate(
        model_factory=LinearRegression, include_interactions=False
    )
    additive_only.fit(observations, subsets=[subset])

    with_interactions = RelativeLinkageAwareSurrogate(
        model_factory=LinearRegression, include_interactions=True
    )
    with_interactions.fit(observations, subsets=[subset])

    x = Genotype(values=(0, 0))
    x_prime = Genotype(values=(1, 1))
    true_delta = 0.0 - 10.0  # f1(x) - f1(x_prime)

    additive_error = abs(additive_only.predict(x, x_prime, subset) - true_delta)
    interaction_error = abs(with_interactions.predict(x, x_prime, subset) - true_delta)
    assert interaction_error < additive_error
    assert interaction_error == pytest.approx(0.0, abs=1e-6)
