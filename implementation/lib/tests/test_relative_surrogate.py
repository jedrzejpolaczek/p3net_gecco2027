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


def _training_error(surrogate, observations, subset) -> float:
    """Sum of squared errors over every ordered pair the surrogate was fit on."""
    total = 0.0
    for a in observations:
        for b in observations:
            if a is b:
                continue
            predicted = surrogate.predict(a.genotype, b.genotype, subset)
            total += (predicted - (a.objectives[0] - b.objectives[0])) ** 2
    return total


def test_interaction_columns_do_not_help_on_a_direction_dependent_pattern():
    """The documented limit of the `include_interactions` ablation.

    `_interaction_features` is a direction-blind "coordinates i and j changed
    together" indicator: it takes the same value for x -> x' and x' -> x, and
    the same value for 00 -> 11 (delta -10 on the AND pattern) as for
    10 -> 01 (delta 0). It therefore adds no representational power here --
    exactly the reason the module's own docstring gives for encoding both
    endpoints instead of a plain diff mask.

    An earlier version of this test asserted the opposite on one query pair
    whose prediction is symmetric, where both variants are exact and the
    comparison only ever saw floating-point noise (it passed on Windows and
    failed on Linux, on values of 1e-15).
    """
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

    additive_error = _training_error(additive_only, observations, subset)
    interaction_error = _training_error(with_interactions, observations, subset)
    assert additive_error > 1.0  # the AND pattern is not additively representable
    assert interaction_error == pytest.approx(additive_error)

    # Both are exact on the fully symmetric query, which is what made the
    # earlier assertion vacuous.
    x, x_prime = Genotype(values=(0, 0)), Genotype(values=(1, 1))
    true_delta = 0.0 - 10.0
    assert additive_only.predict(x, x_prime, subset) == pytest.approx(true_delta)
    assert with_interactions.predict(x, x_prime, subset) == pytest.approx(true_delta)
