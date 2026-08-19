"""Tests for p3net.surrogates.absolute_random_forest: the deterministic,
per-objective Random Forest absolute surrogate (notes/plans/experiments-
bartnik-plan.md, Faza 2) -- two independent sklearn RandomForestRegressor
models (f1, f2), one-hot encoded genotype in, matching
absolute_regressor.py's encoding but with a nonlinear model family able to
fit nonlinear/interaction patterns a linear AbsoluteRegressorSurrogate
cannot."""

from __future__ import annotations

import pytest

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype
from p3net.surrogates.absolute_random_forest import AbsoluteRandomForestSurrogate


def xor_observations() -> list[Observation]:
    """A genuinely nonlinear (XOR-style) pattern in two objectives no
    linear model can fit but a tree ensemble can: f1 is high exactly when
    the two binary coordinates disagree, f2 is the mirror image."""
    data = [
        (Genotype(values=(0, 0)), (0.0, 10.0)),
        (Genotype(values=(0, 1)), (10.0, 0.0)),
        (Genotype(values=(1, 0)), (10.0, 0.0)),
        (Genotype(values=(1, 1)), (0.0, 10.0)),
    ]
    return [Observation(genotype=g, objectives=o) for g, o in data] * 5


def test_fits_and_predicts_both_objectives_independently():
    surrogate = AbsoluteRandomForestSurrogate(n_estimators=20, random_state=0)
    surrogate.fit(xor_observations())
    f1, f2 = surrogate.predict(Genotype(values=(0, 1)))
    assert f1 == pytest.approx(10.0, abs=2.0)
    assert f2 == pytest.approx(0.0, abs=2.0)


def test_captures_a_nonlinear_pattern_a_linear_model_cannot():
    """The whole point of choosing RF over the existing linear
    AbsoluteRegressorSurrogate (plan's Faza 2): must correctly separate
    the XOR pattern's two classes of point, which a single linear model
    fit across all four points cannot (predicts the same value for every
    point, since the linear best fit for XOR is the constant mean)."""
    surrogate = AbsoluteRandomForestSurrogate(n_estimators=50, random_state=1)
    surrogate.fit(xor_observations())
    agree_f1, _ = surrogate.predict(Genotype(values=(0, 0)))
    disagree_f1, _ = surrogate.predict(Genotype(values=(1, 0)))
    assert disagree_f1 - agree_f1 > 5.0


def test_predict_before_fit_raises():
    surrogate = AbsoluteRandomForestSurrogate()
    with pytest.raises(RuntimeError):
        surrogate.predict(Genotype(values=(0, 0)))


def test_fit_rejects_empty_observations():
    surrogate = AbsoluteRandomForestSurrogate()
    with pytest.raises(ValueError):
        surrogate.fit([])


def test_two_independent_model_instances_per_objective():
    """Two separate RandomForestRegressor models, not one multi-output
    model -- per the plan's "dwa osobne modele, f1/f2"."""
    surrogate = AbsoluteRandomForestSurrogate(n_estimators=5, random_state=2)
    surrogate.fit(xor_observations())
    assert surrogate._models[0] is not surrogate._models[1]


def test_deterministic_not_probabilistic_no_uncertainty_api():
    """Explicit v1-scope guard (plan's Faza 5: probabilistic RF is
    explicitly out of scope) -- this surrogate must not expose any
    inter-tree variance / uncertainty estimate."""
    surrogate = AbsoluteRandomForestSurrogate(n_estimators=5, random_state=3)
    surrogate.fit(xor_observations())
    assert not hasattr(surrogate, "predict_std")
    assert not hasattr(surrogate, "predict_with_uncertainty")


def test_same_model_family_usable_by_independent_instances():
    obs = xor_observations()
    surrogate_a = AbsoluteRandomForestSurrogate(n_estimators=5, random_state=4)
    surrogate_b = AbsoluteRandomForestSurrogate(n_estimators=5, random_state=4)
    surrogate_a.fit(obs[:2])
    surrogate_b.fit(obs)
    assert surrogate_a._models is not surrogate_b._models
