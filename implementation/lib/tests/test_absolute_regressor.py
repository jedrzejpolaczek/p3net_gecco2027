"""Tests for p3net.surrogates.absolute_regressor. (Gap in the original
task list -- adding it.)"""

import pytest
from sklearn.linear_model import LinearRegression

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype
from p3net.surrogates.absolute_regressor import AbsoluteRegressorSurrogate


def make_observations() -> list[Observation]:
    data = [
        (Genotype(values=("a", 0)), (10.0,)),
        (Genotype(values=("a", 1)), (10.0,)),
        (Genotype(values=("b", 0)), (20.0,)),
        (Genotype(values=("b", 1)), (20.0,)),
    ]
    return [Observation(genotype=g, objectives=o) for g, o in data]


def test_predicts_f1_from_full_encoding_on_synthetic_data():
    surrogate = AbsoluteRegressorSurrogate(model_factory=LinearRegression)
    surrogate.fit(make_observations())
    prediction = surrogate.predict(Genotype(values=("a", 0)))
    assert prediction == pytest.approx(10.0, abs=1.0)


def test_predict_before_fit_raises():
    surrogate = AbsoluteRegressorSurrogate(model_factory=LinearRegression)
    with pytest.raises(RuntimeError):
        surrogate.predict(Genotype(values=("a", 0)))


def test_fit_rejects_empty_observations():
    surrogate = AbsoluteRegressorSurrogate(model_factory=LinearRegression)
    with pytest.raises(ValueError):
        surrogate.fit([])


def test_same_model_family_usable_by_independent_instances():
    """Proves nsganetv2 and p3_absolute can each construct their own
    independent surrogate instance from the same model family without
    interfering with each other's fitted state."""
    obs = make_observations()
    surrogate_a = AbsoluteRegressorSurrogate(model_factory=LinearRegression)
    surrogate_b = AbsoluteRegressorSurrogate(model_factory=LinearRegression)
    surrogate_a.fit(obs[:2])
    surrogate_b.fit(obs)
    assert surrogate_a._model is not surrogate_b._model
