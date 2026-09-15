"""Regularized (aging) evolution, adapted to two objectives.

Why this arm: regularized evolution (Real, Aggarwal, Huang & Le, 2019,
"Regularized Evolution for Image Classifier Architecture Search") is the
de facto evolutionary baseline in NAS. It is single-objective by design,
so a multi-objective adaptation is this project's own and is documented
here in full (paper, Limitations).

Original algorithm, kept unchanged:
  * a population of P individuals, initialised uniformly at random;
  * each step: sample S individuals uniformly at random from the
    population (tournament), take the best as the parent, apply one
    mutation, evaluate the child, add it to the population;
  * aging: the OLDEST individual is removed (not the worst) -- the
    "regularisation" that gives the method its name.
Mutation: exactly one coordinate is re-sampled to a DIFFERENT value, the
categorical analogue of the paper's single op/connection mutation.

Multi-objective adaptation (the only change): "best in the tournament" is
decided by Pareto rank within the sampled S individuals (nondominated sort
over the sample), ties broken by crowding distance within the lowest-rank
front, then uniformly at random. Removal by age is unchanged, so the
method keeps its defining property.

Hyperparameters: P = 20 to match every other population-based arm in this
project; S = 5 keeps Real et al.'s sample-to-population ratio in the same
range (their S/P = 25/100) at this population size. Not tuned.
"""

from __future__ import annotations

import random
from collections import deque
from dataclasses import dataclass, field

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace

from methods._shared import random_valid_batch
from search_engines.nsga2.crowding_distance import crowding_distance
from search_engines.nsga2.nondominated_sort import fast_nondominated_sort


@dataclass
class RegularizedEvolutionMO:
    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    population_size: int = 20
    sample_size: int = 5
    experiment_type: str = "regularized_evolution_mo"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    _population: deque[Genotype] = field(default_factory=deque, init=False, repr=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if not 1 <= self.sample_size <= self.population_size:
            raise ValueError("sample_size must be between 1 and population_size")

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
        for _ in range(200):
            parent = self._tournament()
            child = self._mutate(parent)
            if not is_valid(child, self.validity):
                continue
            if self.cache.record_proposal(
                child, experiment_type=self.experiment_type, protocol_version=self.protocol_version
            ):
                continue
            return [child]
        # Every mutation tried led to an invalid or already-evaluated genotype.
        return random_valid_batch(
            1,
            self.search_space,
            self.validity,
            self.rng,
            self.cache,
            experiment_type=self.experiment_type,
            protocol_version=self.protocol_version,
        )

    def _tournament(self) -> Genotype:
        sample = self.rng.sample(list(self._population), self.sample_size)
        key = lambda g: self._history[g].objectives  # noqa: E731
        best_front = fast_nondominated_sort(sample, key)[0]
        if len(best_front) == 1:
            return best_front[0]
        distances = crowding_distance(best_front, key)
        top = max(distances.values())
        tied = [best_front[i] for i, d in distances.items() if d == top]
        return self.rng.choice(tied)

    def _mutate(self, genotype: Genotype) -> Genotype:
        i = self.rng.randrange(self.search_space.n)
        alternatives = [v for v in self.search_space.domains[i].values if v != genotype.values[i]]
        if not alternatives:
            return genotype
        return genotype.with_values(indices=[i], new_values=[self.rng.choice(alternatives)])

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            self._history[obs.genotype] = obs
            self._population.append(obs.genotype)
            if len(self._population) > self.population_size:
                self._population.popleft()  # aging: remove the oldest, not the worst
