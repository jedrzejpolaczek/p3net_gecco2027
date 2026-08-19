"""Random search baseline (sanity check).

Own implementation, not a wrapper -- unlike methods/external/*, uniform
random sampling carries no meaningful risk of "getting the algorithm
wrong" relative to a reference implementation, so there is no
reproducibility reason to import it from elsewhere.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity
from p3net.problem.genotype import Genotype, SearchSpace

from methods._shared import random_valid_batch


@dataclass
class RandomSearch:
    """Uniform random sampling over the valid-genotype filter, respecting
    whatever discretised encoding `search_space` uses -- the same one
    every other arm searches, per Fairness controls."""

    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    experiment_type: str = "random_search"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    def propose(self, state: RunState) -> list[Genotype]:
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
