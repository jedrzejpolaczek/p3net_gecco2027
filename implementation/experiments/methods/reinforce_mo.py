"""RL-based NAS baseline: REINFORCE with a factorised categorical policy,
adapted to two objectives.

Why this arm: the RL controller of Zoph & Le (2017, "Neural Architecture
Search with Reinforcement Learning") is the method that started NAS, and a
REINFORCE policy over the genotype's categorical choices is the standard
RL baseline on tabular NAS benchmarks. The recurrent controller of the
original work is replaced by the factorised policy used in benchmark
studies: one independent softmax over each coordinate's values. The policy
covers every coordinate of the joint genotype, architecture and
hyperparameters alike.

Algorithm (per step):
  * sample a genotype from the policy (re-sampling invalid or already
    evaluated genotypes; after 200 failed draws, one uniformly random
    valid unevaluated genotype is proposed instead);
  * once evaluated, compute a scalar reward and apply the REINFORCE update
        theta_i <- theta_i + lr * (reward - baseline) * (onehot(x_i) - pi_i)
    with an exponential moving-average reward baseline.

Multi-objective adaptation (this project's own, documented): the reward is
the negated random-weight Chebyshev scalarisation of the objectives,
normalised by the running minimum and maximum of each objective over
everything evaluated so far, with a fresh weight vector drawn uniformly
from the simplex at every step -- the ParEGO scalarisation, so the policy
is pushed toward different trade-offs over time rather than one fixed
weighting.

Hyperparameters (fixed, not tuned on these benchmarks): learning rate 0.1,
baseline momentum 0.9, logits initialised to zero (uniform policy).
"""

from __future__ import annotations

import math
import random
from dataclasses import dataclass, field

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace

from methods._shared import random_valid_batch


def _softmax(logits: list[float]) -> list[float]:
    top = max(logits)
    exps = [math.exp(v - top) for v in logits]
    total = sum(exps)
    return [e / total for e in exps]


def _simplex_weights(rng: random.Random, n: int) -> list[float]:
    draws = [-math.log(1.0 - rng.random()) for _ in range(n)]
    total = sum(draws)
    return [d / total for d in draws]


@dataclass
class ReinforceMO:
    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    learning_rate: float = 0.1
    baseline_momentum: float = 0.9
    experiment_type: str = "reinforce_mo"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    _logits: list[list[float]] = field(default_factory=list, init=False, repr=False)
    _baseline: float | None = field(default=None, init=False, repr=False)
    _history: list[Observation] = field(default_factory=list, init=False, repr=False)

    def __post_init__(self) -> None:
        self._logits = [[0.0] * len(d.values) for d in self.search_space.domains]

    def _sample(self) -> Genotype:
        values = []
        for domain, logits in zip(self.search_space.domains, self._logits):
            probs = _softmax(logits)
            values.append(self.rng.choices(domain.values, weights=probs, k=1)[0])
        return Genotype(values=tuple(values))

    def propose(self, state: RunState) -> list[Genotype]:
        for _ in range(200):
            candidate = self._sample()
            if not is_valid(candidate, self.validity):
                continue
            if self.cache.record_proposal(
                candidate,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            ):
                continue
            return [candidate]
        return random_valid_batch(
            1,
            self.search_space,
            self.validity,
            self.rng,
            self.cache,
            experiment_type=self.experiment_type,
            protocol_version=self.protocol_version,
        )

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            self._history.append(obs)
            self._reinforce(obs)

    def _reinforce(self, obs: Observation) -> None:
        n_obj = len(obs.objectives)
        lows = [min(o.objectives[j] for o in self._history) for j in range(n_obj)]
        highs = [max(o.objectives[j] for o in self._history) for j in range(n_obj)]
        weights = _simplex_weights(self.rng, n_obj)
        normalised = [
            (obs.objectives[j] - lows[j]) / (highs[j] - lows[j]) if highs[j] > lows[j] else 0.0
            for j in range(n_obj)
        ]
        reward = -max(w * v for w, v in zip(weights, normalised))
        if self._baseline is None:
            self._baseline = reward
        advantage = reward - self._baseline
        self._baseline = (
            self.baseline_momentum * self._baseline + (1.0 - self.baseline_momentum) * reward
        )
        for i, (domain, logits) in enumerate(zip(self.search_space.domains, self._logits)):
            probs = _softmax(logits)
            chosen = domain.values.index(obs.genotype.values[i])
            for k in range(len(logits)):
                grad = (1.0 if k == chosen else 0.0) - probs[k]
                logits[k] += self.learning_rate * advantage * grad
