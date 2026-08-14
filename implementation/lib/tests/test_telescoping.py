"""Tests for p3net.surrogates.telescoping."""

import pytest
from sklearn.linear_model import LinearRegression

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype
from p3net.surrogates.relative_linkage_aware import RelativeLinkageAwareSurrogate
from p3net.surrogates.telescoping import AncestorNotEvaluatedError, ChainStep, telescoped_estimate


def fitted_surrogate():
    data = [
        (Genotype(values=("a", 0)), (10.0,)),
        (Genotype(values=("b", 0)), (20.0,)),
        (Genotype(values=("a", 1)), (10.0,)),
        (Genotype(values=("b", 1)), (20.0,)),
    ]
    observations = [Observation(genotype=g, objectives=o) for g, o in data]
    surrogate = RelativeLinkageAwareSurrogate(model_factory=LinearRegression)
    surrogate.fit(observations, subsets=[frozenset({0})])
    return surrogate, observations


def test_single_step_reduces_to_one_term_formula():
    surrogate, observations = fitted_surrogate()
    ancestor = observations[0]  # ("a", 0), f1 = 10.0
    known = {obs.genotype for obs in observations}
    x_next = Genotype(values=("b", 0))
    chain = [ChainStep(x_prev=ancestor.genotype, x_next=x_next, subset=frozenset({0}))]

    estimate = telescoped_estimate(ancestor, chain, surrogate, known)
    direct = ancestor.objectives[0] - surrogate.predict(ancestor.genotype, x_next, frozenset({0}))
    assert estimate == pytest.approx(direct)


def test_multi_step_chain_sums_correctly():
    surrogate, observations = fitted_surrogate()
    ancestor = observations[0]
    known = {obs.genotype for obs in observations}

    x1 = Genotype(values=("b", 0))
    x2 = Genotype(values=("a", 0))
    chain = [
        ChainStep(x_prev=ancestor.genotype, x_next=x1, subset=frozenset({0})),
        ChainStep(x_prev=x1, x_next=x2, subset=frozenset({0})),
    ]
    estimate = telescoped_estimate(ancestor, chain, surrogate, known)

    d1 = surrogate.predict(ancestor.genotype, x1, frozenset({0}))
    d2 = surrogate.predict(x1, x2, frozenset({0}))
    expected = ancestor.objectives[0] - d1 - d2
    assert estimate == pytest.approx(expected)


def test_ancestor_must_come_from_h_t():
    surrogate, observations = fitted_surrogate()
    known = {obs.genotype for obs in observations}
    fake_ancestor = Observation(genotype=Genotype(values=("z", 9)), objectives=(0.0,))
    chain = [
        ChainStep(
            x_prev=fake_ancestor.genotype,
            x_next=Genotype(values=("a", 0)),
            subset=frozenset({0}),
        )
    ]
    with pytest.raises(AncestorNotEvaluatedError):
        telescoped_estimate(fake_ancestor, chain, surrogate, known)
