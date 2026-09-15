"""NSGANetV2 (primary baseline): NSGA-II + absolute regressor surrogate,
discretised Theta.

Known simplification: only the shared discretised Theta encoding is
implemented here. The nsganetv2_continuous control variant (native
real-valued Theta, isolating the effect of discretisation itself from the
search engine/surrogate) needs a parallel real-valued crossover operator
this class doesn't have -- not yet implemented, tracked in CHANGELOG.md's
"Known gaps" section rather than silently skipped.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from p3net.harness.decision_log import DecisionLog
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.surrogates.absolute_regressor import AbsoluteRegressorSurrogate

from methods._shared import mutate, random_valid_batch, select_survivors, uniform_crossover


@dataclass
class NSGANetV2:
    """NSGA-II paired with an absolute regressor surrogate: generates a
    larger pool of offspring than needed per generation, screens them with
    a surrogate freshly fit on H_t, and only proposes the most promising
    subset for full evaluation -- mirroring NSGANetV2's efficiency
    mechanism. Searches the SAME discretised Theta encoding as P3Net
    (Fairness controls)."""

    search_space: SearchSpace
    validity: Validity
    model_factory: Callable[[], Any]
    rng: random.Random
    population_size: int = 20
    offspring_pool_multiplier: int = 3
    objective_index: int = 0
    experiment_type: str = "nsganetv2"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    _population: list[Genotype] = field(default_factory=list, init=False, repr=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)
    #: Uniform sample of predictor selections, checked against the benchmark
    #: after the run; never influences the search.
    decision_log: DecisionLog = field(default_factory=DecisionLog, init=False, repr=False)

    def propose(self, state: RunState) -> list[Genotype]:
        if len(self._population) < self.population_size:
            return random_valid_batch(
                self.population_size - len(self._population),
                self.search_space,
                self.validity,
                self.rng,
                self.cache,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )

        pool = self._generate_offspring_pool(self.population_size * self.offspring_pool_multiplier)
        if not pool:
            return []

        surrogate = AbsoluteRegressorSurrogate(model_factory=self.model_factory)
        surrogate.fit(list(self._history.values()), objective_index=self.objective_index)
        predicted = {g: surrogate.predict(g) for g in pool}
        pool.sort(key=predicted.__getitem__)
        selected = pool[: self.population_size]
        for rank, g in enumerate(pool):
            self.decision_log.selection(
                source="predictor",
                candidate=g,
                predicted_f1=predicted[g],
                accepted=rank < self.population_size,
            )

        return [
            g
            for g in selected
            if not self.cache.record_proposal(
                g, experiment_type=self.experiment_type, protocol_version=self.protocol_version
            )
        ]

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            self._history[obs.genotype] = obs
            if obs.genotype not in self._population:
                self._population.append(obs.genotype)
        if len(self._population) > self.population_size:
            self._population = select_survivors(
                self._population, self._history, self.population_size
            )

    def _generate_offspring_pool(self, n: int) -> list[Genotype]:
        pool: list[Genotype] = []
        attempts = 0
        while len(pool) < n and attempts < n * 20 + 50:
            attempts += 1
            parent_a, parent_b = self.rng.sample(self._population, 2)
            child = uniform_crossover(parent_a, parent_b, self.rng)
            child = mutate(child, self.search_space, self.rng, rate=0.1)
            if not is_valid(child, self.validity):
                continue
            if child in pool:
                continue
            if self.cache.record_proposal(
                child, experiment_type=self.experiment_type, protocol_version=self.protocol_version
            ):
                continue
            pool.append(child)
        return pool
