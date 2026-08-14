"""P3 + absolute regressor surrogate (surrogate-only ablation, isolating
linkage-aware design from the P3 engine itself)."""

from __future__ import annotations

import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives, pareto_front
from p3net.search_engines.p3.linkage_tree import build_linkage_tree
from p3net.search_engines.p3.optimal_mixing import SweepState
from p3net.surrogates.absolute_regressor import AbsoluteRegressorSurrogate

from methods._shared import random_valid_batch


@dataclass
class P3Absolute:
    """P3's optimal-mixing sweep scored by an absolute regressor
    (NSGANetV2 style) instead of the relative, linkage-aware delta_hat_F
    -- isolates the contribution of the linkage-aware surrogate design
    from the contribution of the P3 engine itself. Acceptance rule adapted
    for an absolute (not relative) prediction: accept iff the predicted f1
    of the candidate is no worse than the current individual's f1/predicted
    value -- the same "no worsening" spirit as P3Net's zero-threshold
    default, applied to an absolute rather than relative quantity.
    """

    search_space: SearchSpace
    validity: Validity
    model_factory: Callable[[], Any]
    rng: random.Random
    population_size: int = 20
    kappa: int | None = None
    objective_index: int = 0
    experiment_type: str = "p3_absolute"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    _population: list[Genotype] = field(default_factory=list, init=False, repr=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.kappa is None:
            n = max(self.search_space.n, 2)
            self.kappa = 2 * math.ceil(math.log2(n))

    def propose(self, state: RunState) -> list[Genotype]:
        if len(self._population) < self.population_size:
            return self._bootstrap_proposals()
        return self._sweep_proposals()

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
            self._population.sort(key=lambda g: self._history[g].objectives[self.objective_index])
            self._population = self._population[: self.population_size]

    def _bootstrap_proposals(self) -> list[Genotype]:
        needed = self.population_size - len(self._population)
        return self._random_valid_batch(needed)

    def _random_valid_batch(self, n: int) -> list[Genotype]:
        return random_valid_batch(
            n,
            self.search_space,
            self.validity,
            self.rng,
            self.cache,
            experiment_type=self.experiment_type,
            protocol_version=self.protocol_version,
        )

    def _sweep_proposals(self) -> list[Genotype]:
        linkage_root = build_linkage_tree(self._population)
        surrogate = AbsoluteRegressorSurrogate(model_factory=self.model_factory)
        surrogate.fit(list(self._history.values()), objective_index=self.objective_index)

        candidate_estimates: dict[Genotype, Objectives] = {}
        for parent in self._population:
            current_value = self._history[parent].objectives[self.objective_index]
            current_estimate: Objectives = self._history[parent].objectives
            sweep = SweepState.start(parent, linkage_root, self._population, self.rng)
            chain_depth = 0
            while not sweep.done:
                proposal = sweep.propose()
                if not is_valid(proposal.candidate, self.validity):
                    sweep.reject(proposal)
                    continue
                predicted = surrogate.predict(proposal.candidate)
                if predicted <= current_value:
                    sweep.accept(proposal)
                    chain_depth += 1
                    current_value = predicted
                    current_estimate = tuple(
                        predicted if i == self.objective_index else current_estimate[i]
                        for i in range(len(current_estimate))
                    )
                    if chain_depth >= self.kappa:
                        break
                else:
                    sweep.reject(proposal)
            candidate_estimates[sweep.current] = current_estimate

        candidates = [g for g in candidate_estimates if is_valid(g, self.validity)]
        if not candidates:
            return self._random_valid_batch(1)
        selected = pareto_front(candidates, lambda g: candidate_estimates[g])
        proposals = [
            g
            for g in selected
            if not self.cache.record_proposal(
                g, experiment_type=self.experiment_type, protocol_version=self.protocol_version
            )
        ]
        if proposals:
            return proposals
        # Stall: every candidate this sweep produced was already fully
        # evaluated (same class of issue documented and fixed in
        # p3net.methods.p3net.P3Net's module docstring, simplification 3)
        # -- inject fresh random diversity rather than halting the run.
        return self._random_valid_batch(1)
