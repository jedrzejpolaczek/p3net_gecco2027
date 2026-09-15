"""Neural-predictor NAS baseline: BANANAS, adapted to two objectives.

Why this arm: BANANAS (White, Neiswanger & Savani, 2021, "BANANAS: Bayesian
Optimization with Neural Architectures for Neural Architecture Search") is
the reference neural-predictor method on tabular NAS benchmarks. It
represents the "learned performance predictor" family independently of
NSGANetV2, whose predictor is paired with an evolutionary engine.

Algorithm, as in the original, on this project's genotype:
  * initial design: `n_initial` uniformly random valid genotypes (10, the
    original's default);
  * predictor: an ensemble of `ensemble_size` (5) independently seeded
    fully connected networks trained on the evaluated genotypes;
  * acquisition: independent Thompson sampling -- for every candidate
    independently, a value is drawn from a Gaussian with the ensemble's
    mean and standard deviation for that candidate;
  * acquisition optimisation by mutation: candidates are one- and
    two-coordinate mutations of the current Pareto set, plus uniformly
    random genotypes, restricted to valid unevaluated genotypes.
The original path encoding is specific to cell DAGs and cannot represent
training hyperparameters; here the encoding is the one-hot encoding of the
whole joint genotype, so the predictor sees architecture and
hyperparameters alike.

Multi-objective adaptation (this project's own, documented): each ensemble
member predicts both objectives; the Thompson-sampled prediction is
scalarised with a random-weight Chebyshev function (weights drawn uniformly
from the simplex every step, objectives normalised by the observed range) --
the ParEGO scalarisation used by the other scalarising arms. One genotype is
proposed per step.

Predictor: sklearn MLPRegressor with the original's 10 hidden layers of
width 20, Adam, learning rate 0.01, 200 iterations. Not tuned.
"""

from __future__ import annotations

import math
import random
import warnings
from dataclasses import dataclass, field

import numpy as np
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import pareto_front

from methods._shared import random_valid_batch


@dataclass
class BananasMO:
    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    n_initial: int = 10
    ensemble_size: int = 5
    n_mutation_candidates: int = 100
    n_random_candidates: int = 100
    hidden_layers: int = 10
    hidden_width: int = 20
    learning_rate: float = 0.01
    max_iter: int = 200
    experiment_type: str = "bananas_mo"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    fit_seconds: float = field(default=0.0, init=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)
    _order: list[Genotype] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._index = [
            {value: i for i, value in enumerate(domain.values)}
            for domain in self.search_space.domains
        ]
        self._width = sum(len(d.values) for d in self.search_space.domains)

    def _encode(self, genotypes: list[Genotype]) -> np.ndarray:
        X = np.zeros((len(genotypes), self._width))
        for row, g in enumerate(genotypes):
            offset = 0
            for i, value in enumerate(g.values):
                X[row, offset + self._index[i][value]] = 1.0
                offset += len(self._index[i])
        return X

    def propose(self, state: RunState) -> list[Genotype]:
        if len(self._history) < self.n_initial:
            return random_valid_batch(
                1,
                self.search_space,
                self.validity,
                self.rng,
                self.cache,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
        pool = self._candidates()
        if not pool:
            return random_valid_batch(
                1,
                self.search_space,
                self.validity,
                self.rng,
                self.cache,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
        ensemble = self._fit_ensemble()
        Y = self._objectives()
        lows, highs = Y.min(axis=0), Y.max(axis=0)
        span = np.where(highs > lows, highs - lows, 1.0)
        X_pool = self._encode(pool)
        predictions = np.stack([member.predict(X_pool) for member in ensemble])  # E x N x M
        mean, std = predictions.mean(axis=0), predictions.std(axis=0)
        noise = np.random.default_rng(self.rng.randrange(2**31)).standard_normal(mean.shape)
        sampled = mean + std * noise
        draws = [-math.log(1.0 - self.rng.random()) for _ in range(Y.shape[1])]
        weights = np.array(draws) / sum(draws)
        scores = np.max(weights * (sampled - lows) / span, axis=1)
        best = pool[int(np.argmin(scores))]
        self.cache.record_proposal(
            best, experiment_type=self.experiment_type, protocol_version=self.protocol_version
        )
        return [best]

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            self._history[obs.genotype] = obs
            self._order.append(obs.genotype)

    def _objectives(self) -> np.ndarray:
        return np.array([self._history[g].objectives for g in self._order], dtype=float)

    def _fit_ensemble(self) -> list[_Rescaled]:
        """Every member is trained on the same data with its own seed, as in
        the original; the spread between members is the uncertainty used
        by independent Thompson sampling."""
        import time

        from sklearn.neural_network import MLPRegressor

        Y = self._objectives()
        lows, highs = Y.min(axis=0), Y.max(axis=0)
        span = np.where(highs > lows, highs - lows, 1.0)
        X = self._encode(self._order)
        target = (Y - lows) / span
        members = []
        started = time.perf_counter()
        for _ in range(self.ensemble_size):
            model = MLPRegressor(
                hidden_layer_sizes=(self.hidden_width,) * self.hidden_layers,
                solver="adam",
                learning_rate_init=self.learning_rate,
                max_iter=self.max_iter,
                random_state=self.rng.randrange(2**31),
            )
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(X, target)
            members.append(_Rescaled(model, lows, span))
        self.fit_seconds += time.perf_counter() - started
        return members

    def _candidates(self) -> list[Genotype]:
        pool: dict[Genotype, None] = {}
        front = pareto_front(list(self._order), lambda g: self._history[g].objectives)
        for _ in range(self.n_mutation_candidates):
            g = self.rng.choice(front)
            for _ in range(self.rng.choice((1, 2))):
                i = self.rng.randrange(self.search_space.n)
                alternatives = [v for v in self.search_space.domains[i].values if v != g.values[i]]
                if alternatives:
                    g = g.with_values(indices=[i], new_values=[self.rng.choice(alternatives)])
            pool[g] = None
        for _ in range(self.n_random_candidates):
            pool[self.search_space.sample_uniform(self.rng)] = None
        return [
            g
            for g in pool
            if g not in self._history
            and is_valid(g, self.validity)
            and not self.cache.has(
                g, experiment_type=self.experiment_type, protocol_version=self.protocol_version
            )
        ]


class _Rescaled:
    """Undo the training-time normalisation so predictions are in objective units."""

    def __init__(self, model, lows: np.ndarray, span: np.ndarray) -> None:
        self._model, self._lows, self._span = model, lows, span

    def predict(self, X: np.ndarray) -> np.ndarray:
        return self._model.predict(X).reshape(len(X), -1) * self._span + self._lows
