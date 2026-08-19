"""NSGA-Net (engine-only ablation, NSGA-II side -- no surrogate, every
candidate fully trained/evaluated)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace

from methods._shared import mutate, random_valid_batch, select_survivors, uniform_crossover


@dataclass
class NSGANet:
    """Plain NSGA-II: fast nondominated sort + crowding-distance survivor
    selection, uniform crossover + per-coordinate mutation as variation,
    every candidate fully evaluated (no surrogate anywhere in the loop).
    The engine-only ablation on the NSGA-II side, symmetric to
    methods.p3_alone.P3Alone on the P3 side."""

    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    population_size: int = 20
    mutation_rate: float = 0.1
    experiment_type: str = "nsga_net"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    _population: list[Genotype] = field(default_factory=list, init=False, repr=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)

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

        offspring: list[Genotype] = []
        needed = self.population_size
        attempts = 0
        while len(offspring) < needed and attempts < needed * 50 + 50:
            attempts += 1
            parent_a, parent_b = self.rng.sample(self._population, 2)
            child = uniform_crossover(parent_a, parent_b, self.rng)
            child = mutate(child, self.search_space, self.rng, self.mutation_rate)
            if not is_valid(child, self.validity):
                continue
            if child in offspring:
                continue
            if self.cache.record_proposal(
                child, experiment_type=self.experiment_type, protocol_version=self.protocol_version
            ):
                continue
            offspring.append(child)
        return offspring

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
