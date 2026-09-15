"""Multi-objective local search baseline: Pareto Local Search (PLS).

Why this arm: White et al. (2021, "Local Search is a Remarkably Strong
Baseline for Neural Architecture Search") show plain local search is
competitive with far more elaborate NAS methods on small cell spaces --
exactly this benchmark family -- and den Ottelander et al. (2021) and
Bartnik (2026) both compare linkage-learning EAs against a multi-objective
local search. Without it, "P3 beats a simple method" is untested.

Algorithm: Pareto Local Search (Paquete, Chiarandini & Stuetzle, 2004), the
standard multi-objective extension of local search.
  * An archive holds every evaluated genotype not dominated by another.
  * Repeatedly pick an archive member whose neighbourhood has not been
    explored yet (uniformly at random) and evaluate its neighbours: every
    genotype differing in exactly one coordinate, in random order.
  * Newly evaluated genotypes update the archive as they arrive, so an
    improving neighbour becomes explorable itself.
  * When every archive member has been explored (a Pareto local optimum),
    restart from a uniformly random valid genotype.
One genotype is proposed per call, so the budget is spent exactly.

No hyperparameters: the neighbourhood (one-coordinate changes) and the
restart rule are the textbook definition.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import dominates

from methods._shared import random_valid_batch


@dataclass
class MOLocalSearch:
    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    experiment_type: str = "mo_ls"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    restarts: int = field(default=0, init=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)
    _archive: list[Genotype] = field(default_factory=list, init=False, repr=False)
    _explored: set[Genotype] = field(default_factory=set, init=False, repr=False)
    _neighbours: list[Genotype] = field(default_factory=list, init=False, repr=False)

    def propose(self, state: RunState) -> list[Genotype]:
        while True:
            while self._neighbours:
                candidate = self._neighbours.pop()
                if not is_valid(candidate, self.validity):
                    continue
                if self.cache.record_proposal(
                    candidate,
                    experiment_type=self.experiment_type,
                    protocol_version=self.protocol_version,
                ):
                    continue
                return [candidate]

            unexplored = [g for g in self._archive if g not in self._explored]
            if not unexplored:
                # Empty archive (start) or a Pareto local optimum: restart.
                if self._history:
                    self.restarts += 1
                return random_valid_batch(
                    1,
                    self.search_space,
                    self.validity,
                    self.rng,
                    self.cache,
                    experiment_type=self.experiment_type,
                    protocol_version=self.protocol_version,
                )
            centre = self.rng.choice(unexplored)
            self._explored.add(centre)
            self._neighbours = self._neighbourhood(centre)

    def _neighbourhood(self, genotype: Genotype) -> list[Genotype]:
        neighbours: list[Genotype] = []
        for i, domain in enumerate(self.search_space.domains):
            for value in domain.values:
                if value != genotype.values[i]:
                    neighbours.append(genotype.with_values(indices=[i], new_values=[value]))
        self.rng.shuffle(neighbours)
        return neighbours

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            self._history[obs.genotype] = obs
            if any(dominates(self._history[a].objectives, obs.objectives) for a in self._archive):
                continue
            self._archive = [
                a
                for a in self._archive
                if not dominates(obs.objectives, self._history[a].objectives)
            ]
            self._archive.append(obs.genotype)
