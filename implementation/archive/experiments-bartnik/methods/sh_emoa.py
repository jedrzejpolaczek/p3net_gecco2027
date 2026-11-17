"""SH-EMOA (Successive Halving Evolutionary MultiObjective Algorithm).

Own implementation, not a wrapper. There is no published SH-EMOA package
to wrap: the original paper's own reference code
(automl/multi-obj-baselines, guerreroviu2021bagofbaselines's code
release, baselines/methods/shemoa/{shemoa,member}.py) is a self-contained
algorithm that does not use pymoo or any other multi-objective library.
Verified by reading that reference implementation directly, not guessed:
a (mu+lambda) evolutionary loop -- uniform mutation/crossover, tournament
parent selection, and survivor selection by non-dominated sort followed
by removing the member with the smallest hypervolume contribution from
the worst front. That hypervolume-contribution removal is exactly
SMS-EMOA's survivor-selection mechanism, which is why this project's
paper draft describes SH-EMOA as "a multi objective evolutionary
algorithm built on SMS-EMOA" -- the shared principle, not shared code.

Adapted here to this project's Genotype/SearchSpace/EvaluationCache types
and generalised to an arbitrary number of objectives (the reference's own
hypervolume-contribution computation is hardcoded to exactly 2 objectives
and one specific toy problem's reference point; this uses
p3net.metrics.hypervolume, which is not).

Known gap, tracked rather than silently dropped: only the (mu+lambda)
EMOA half of the real algorithm is implemented. The "SH" (successive
halving / multi-fidelity budget escalation) half re-evaluates the whole
population at increasing training-epoch budgets over the course of a
run. This project's harness (p3net.harness.Runner /
substrates.Substrate) only supports single-fidelity (r_K) full
evaluations, so there is no budget dimension to escalate over yet --
wiring real multi-fidelity querying is a harness-level change (the same
open question already flagged in methods/external/mo_bohb.py's docstring
for MO-BOHB), not guessed at here.
"""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.metrics.hypervolume import hypervolume
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives

from methods._shared import mutate, random_valid_batch, uniform_crossover
from search_engines.nsga2.nondominated_sort import fast_nondominated_sort


def _reference_point(points: list[Objectives]) -> Objectives:
    """A reference point weakly worse than every point in `points`, for
    hypervolume-contribution scoring: the per-objective max (the nadir),
    plus a small margin so no point sits exactly on the boundary."""
    dims = len(points[0])
    maxima = [max(p[j] for p in points) for j in range(dims)]
    minima = [min(p[j] for p in points) for j in range(dims)]
    margins = [max(1e-9, (maxima[j] - minima[j]) * 0.01) for j in range(dims)]
    return tuple(maxima[j] + margins[j] for j in range(dims))


def _survive(
    population: list[Genotype], history: dict[Genotype, Observation], target_size: int
) -> list[Genotype]:
    """Non-dominated sort, keep whole fronts while they fit within
    target_size, then trim the first front that would overflow by
    repeatedly removing whichever member contributes the LEAST
    hypervolume to that front (relative to a reference point computed
    over the whole population) -- SMS-EMOA's survivor-selection rule."""
    if len(population) <= target_size:
        return list(population)

    fronts = fast_nondominated_sort(population, lambda g: history[g].objectives)
    survivors: list[Genotype] = []
    for front in fronts:
        if len(survivors) + len(front) <= target_size:
            survivors.extend(front)
            continue

        remaining = list(front)
        reference = _reference_point([history[g].objectives for g in population])
        keep_count = target_size - len(survivors)
        while len(remaining) > keep_count:
            front_hv = hypervolume([history[g].objectives for g in remaining], reference)
            contributions = {}
            for g in remaining:
                without = [history[other].objectives for other in remaining if other != g]
                contributions[g] = front_hv - hypervolume(without, reference)
            worst = min(remaining, key=lambda g: contributions[g])
            remaining.remove(worst)
        survivors.extend(remaining)
        break
    return survivors


@dataclass
class SHEMOA:
    """The (mu+lambda) EMOA core of SH-EMOA (see module docstring for
    scope). Each step past the initial random bootstrap: select a parent
    by tournament (ranked by non-domination front, ties broken by
    hypervolume contribution), produce one child by mutation or uniform
    crossover, propose it for a real evaluation, then restore
    population_size via _survive once the result comes back."""

    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    population_size: int = 10
    mutation_rate: float = 0.2
    crossover_probability: float = 0.5
    tournament_size: int = 3
    experiment_type: str = "sh_emoa"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    _population: list[Genotype] = field(default_factory=list, init=False, repr=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)
    _front_rank: dict[Genotype, int] = field(default_factory=dict, init=False, repr=False)

    def propose(self, state: RunState) -> list[Genotype]:
        if len(self._population) < self.population_size:
            needed = self.population_size - len(self._population)
            return random_valid_batch(
                needed,
                self.search_space,
                self.validity,
                self.rng,
                self.cache,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
        return self._offspring_batch()

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
            self._population = _survive(self._population, self._history, self.population_size)
        self._update_front_rank()

    def _update_front_rank(self) -> None:
        if not self._population:
            self._front_rank = {}
            return
        fronts = fast_nondominated_sort(self._population, lambda g: self._history[g].objectives)
        self._front_rank = {g: rank for rank, front in enumerate(fronts) for g in front}

    def _offspring_batch(self) -> list[Genotype]:
        attempts = 0
        while attempts < 200:
            attempts += 1
            parent = self._tournament_select()
            if self.rng.random() < self.crossover_probability and len(self._population) > 1:
                partner = self._tournament_select()
                child = uniform_crossover(parent, partner, self.rng)
            else:
                child = mutate(parent, self.search_space, self.rng, self.mutation_rate)
            if not is_valid(child, self.validity):
                continue
            if self.cache.record_proposal(
                child, experiment_type=self.experiment_type, protocol_version=self.protocol_version
            ):
                continue
            return [child]
        # Stall: 200 mutation/crossover attempts produced nothing but
        # duplicates or invalid candidates -- same class of issue as
        # p3net.methods.p3net.P3Net's documented stall recovery. Inject
        # fresh random diversity rather than halting the run.
        return random_valid_batch(
            1,
            self.search_space,
            self.validity,
            self.rng,
            self.cache,
            experiment_type=self.experiment_type,
            protocol_version=self.protocol_version,
        )

    def _tournament_select(self) -> Genotype:
        k = min(self.tournament_size, len(self._population))
        contenders = self.rng.sample(self._population, k)
        return min(contenders, key=lambda g: self._front_rank.get(g, 0))
