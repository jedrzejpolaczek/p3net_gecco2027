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
