"""Deterministic, per-objective Random Forest absolute surrogate
(notes/plans/experiments-bartnik-plan.md, Faza 2) -- the surrogate half of
`experiments/methods/bartnik_p3.py`'s reconstruction of Bartnik's
architecture-only NAS-Bench-201 result.

Two independent `sklearn.ensemble.RandomForestRegressor` models, one per
objective (f1, f2), each fit on the same one-hot genotype encoding
`absolute_regressor.AbsoluteRegressorSurrogate` already uses -- deliberately
sharing `_encoding.py` rather than duplicating it. Chosen over that
existing linear surrogate specifically for its ability to fit nonlinear/
interaction patterns (plan's Faza 2 rationale over SVR/MLP/GBoost: no
kernel to tune, no cross-run instability, simpler than GBoost +
quantile-loss for a future probabilistic variant).

Deterministic only -- no inter-tree variance / uncertainty estimate is
exposed. A probabilistic variant (RF with inter-tree std as a Gaussian
proxy) is explicitly out of v1 scope (plan's Faza 5).
"""

from __future__ import annotations

from dataclasses import dataclass, field

from sklearn.ensemble import RandomForestRegressor

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import Objectives
from p3net.surrogates._encoding import build_vocab, one_hot


@dataclass
class AbsoluteRandomForestSurrogate:
    n_estimators: int = 100
    random_state: int | None = None
    _models: list[RandomForestRegressor] | None = field(default=None, init=False, repr=False)
    _vocab: list[dict] | None = field(default=None, init=False, repr=False)

    def fit(self, observations: list[Observation]) -> None:
        if not observations:
            raise ValueError("cannot fit an absolute Random Forest surrogate on zero observations")
        self._vocab = build_vocab(observations)
        X = [one_hot(obs.genotype, self._vocab) for obs in observations]
        n_objectives = len(observations[0].objectives)
        self._models = []
        for objective_index in range(n_objectives):
            y = [obs.objectives[objective_index] for obs in observations]
            model = RandomForestRegressor(
                n_estimators=self.n_estimators, random_state=self.random_state
            )
            model.fit(X, y)
            self._models.append(model)

    def predict(self, genotype: Genotype) -> Objectives:
        if self._models is None or self._vocab is None:
            raise RuntimeError("AbsoluteRandomForestSurrogate.predict called before fit")
        x = one_hot(genotype, self._vocab)
        return tuple(float(model.predict([x])[0]) for model in self._models)
