"""Absolute regressor surrogate (NSGANetV2-style; also used by the
P3+absolute ablation)."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype
from p3net.surrogates._encoding import build_vocab, one_hot


@dataclass
class AbsoluteRegressorSurrogate:
    """Predicts f1(x) directly from the full genotype encoding. Used by
    ../../../../experiments/methods/nsganetv2.py and
    ../../../../experiments/methods/p3_absolute.py; both must use the same
    model family so the P3-vs-NSGA-II ablation isolates the search engine,
    not the surrogate."""

    model_factory: Callable[[], Any]
    _model: Any = field(default=None, init=False, repr=False)
    _vocab: list[dict[Any, int]] | None = field(default=None, init=False, repr=False)

    def fit(self, observations: list[Observation], *, objective_index: int = 0) -> None:
        if not observations:
            raise ValueError("cannot fit an absolute regressor on zero observations")
        self._vocab = build_vocab(observations)
        X = [one_hot(obs.genotype, self._vocab) for obs in observations]
        y = [obs.objectives[objective_index] for obs in observations]
        self._model = self.model_factory()
        self._model.fit(X, y)

    def predict(self, genotype: Genotype) -> float:
        if self._vocab is None:
            raise RuntimeError("AbsoluteRegressorSurrogate.predict called before fit")
        x = one_hot(genotype, self._vocab)
        return float(self._model.predict([x])[0])
