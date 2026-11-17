"""P3 + absolute regressor surrogate (surrogate-only ablation, isolating
linkage-aware design from the P3 engine itself).

Shares P3Net's own Pyramid engine (2026-08-18, Phase 3 of the pyramid/
surrogate fix plan; Conclusions) rather than a flat, fixed-size population
-- the Baselines paragraph already describes this ablation as isolating
"only the surrogate", which was not actually true before this change: a
flat population is itself a different search-loop mechanic from P3Net's
growing pyramid, confounding surrogate type with population-management
engine. Mirrors p3net.methods.p3net.P3Net's own propose/update/
_bootstrap_proposals/_sweep_proposals/_update_level_population shape
directly, substituting AbsoluteRegressorSurrogate for
RelativeLinkageAwareSurrogate and an absolute (not telescoped/relative)
acceptance rule: accept iff the predicted f1 of the candidate is no worse
than the current individual's f1/predicted value -- the same "no
worsening" spirit as P3Net's zero-threshold default, applied to an
absolute rather than relative quantity, with no telescoping construction
needed since an absolute regressor predicts f1 directly.
"""

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
from p3net.problem.objectives import Objectives, dominates, pareto_front, select_survivors
from p3net.search_engines.p3.linkage_tree import build_linkage_tree
from p3net.search_engines.p3.optimal_mixing import SweepState
from p3net.search_engines.p3.pyramid import Pyramid, PyramidLevel
from p3net.surrogates.absolute_regressor import AbsoluteRegressorSurrogate

from methods._shared import random_valid_batch


@dataclass
class P3Absolute:
    """P3's optimal-mixing sweep, on the same growing population pyramid
    P3Net uses, scored by an absolute regressor (NSGANetV2 style) instead
    of the relative, linkage-aware delta_hat_F -- isolates the
    contribution of the linkage-aware surrogate design from the
    contribution of the P3 engine itself, now including its population
    management, not only its variation operator.
    """

    search_space: SearchSpace
    validity: Validity
    model_factory: Callable[[], Any]
    rng: random.Random
    growth_factor: int = 2
    kappa: int | None = None
    objective_index: int = 0
    experiment_type: str = "p3_absolute"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    _pyramid: Pyramid = field(init=False, repr=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)

    #: Same diagnostics P3Net's own Pyramid engine carries (Results,
    #: "Diagnostics: population-pyramid bootstrap share") -- kept to the
    #: three that verify the engine swap itself took effect (a real
    #: post-refactor check, not just a renamed class), not the surrogate-
    #: specific ones (chain_depth_log, level_size_log, fit/tree timings)
    #: that assume P3Net's telescoping construction, which this class does
    #: not have.
    bootstrap_proposals: int = field(default=0, init=False, repr=False)
    mixing_proposals: int = field(default=0, init=False, repr=False)
    population_snapshots: list[list[Genotype]] = field(
        default_factory=list, init=False, repr=False
    )

    def __post_init__(self) -> None:
        if self.kappa is None:
            n = max(self.search_space.n, 2)
            self.kappa = 2 * math.ceil(math.log2(n))
        self._pyramid = Pyramid(growth_factor=self.growth_factor)
        self._pyramid.add_level()

    @property
    def _level(self) -> PyramidLevel:
        return self._pyramid.levels[-1]

    @property
    def _level_index(self) -> int:
        return len(self._pyramid.levels) - 1

    # -- harness.Method protocol ------------------------------------------

    def propose(self, state: RunState) -> list[Genotype]:
        if self._pyramid.all_stalled:
            self._warm_start_level(self._pyramid.add_level())
        level = self._level
        if len(level.population) < level.size:
            return self._bootstrap_proposals(level)
        return self._sweep_proposals(level)

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            self._history[obs.genotype] = obs
        self._update_level_population(self._level, self._level_index, new_observations)

    def _update_level_population(
        self, level: PyramidLevel, level_index: int, new_observations: list[Observation]
    ) -> None:
        """The bootstrap/promote/truncate logic for one pyramid level's
        share of one update() call -- identical shape to P3Net's own."""
        bootstrapping = len(level.population) < level.size

        if bootstrapping:
            for obs in new_observations:
                if obs.genotype not in level.population:
                    level.population.append(obs.genotype)
            if len(level.population) >= level.size:
                self._seed_best_objectives(level)
        else:
            best_obs = new_observations[0]
            for obs in new_observations[1:]:
                if dominates(obs.objectives, best_obs.objectives):
                    best_obs = obs
            population_objectives = [self._history[g].objectives for g in level.population]
            self._pyramid.promote(
                level_index,
                best_obs.genotype,
                best_obs.objectives,
                population_objectives=population_objectives,
            )
            for obs in new_observations:
                if obs.genotype not in level.population:
                    level.population.append(obs.genotype)

        if len(level.population) > level.size:
            level.population = select_survivors(
                level.population, lambda g: self._history[g].objectives, level.size
            )

        self.population_snapshots.append(list(level.population))

    # -- internals ---------------------------------------------------------

    def _warm_start_level(self, level: PyramidLevel) -> None:
        """Same as P3Net's own (module docstring there): seed a newly-
        grown level with H_t's current nondominated front rather than
        starting empty -- zero fresh evaluation cost, since these
        genotypes are already evaluated."""
        if not self._history:
            return
        elites = pareto_front(list(self._history.keys()), lambda g: self._history[g].objectives)
        if len(elites) > level.size:
            elites = select_survivors(elites, lambda g: self._history[g].objectives, level.size)
        level.population = list(elites)
        self._seed_best_objectives(level)

    def _seed_best_objectives(self, level: PyramidLevel) -> None:
        best: Genotype | None = None
        for g in level.population:
            obj = self._history[g].objectives
            if best is None or dominates(obj, self._history[best].objectives):
                best = g
        if best is not None:
            level.best_objectives = self._history[best].objectives

    def _bootstrap_proposals(self, level: PyramidLevel) -> list[Genotype]:
        needed = level.size - len(level.population)
        proposals = self._random_valid_batch(needed)
        self.bootstrap_proposals += len(proposals)
        return proposals

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

    def _sweep_proposals(self, level: PyramidLevel) -> list[Genotype]:
        linkage_root = build_linkage_tree(level.population)
        surrogate = AbsoluteRegressorSurrogate(model_factory=self.model_factory)
        surrogate.fit(list(self._history.values()), objective_index=self.objective_index)

        candidate_estimates: dict[Genotype, Objectives] = {}
        for parent in level.population:
            current_value = self._history[parent].objectives[self.objective_index]
            current_estimate: Objectives = self._history[parent].objectives
            sweep = SweepState.start(parent, linkage_root, level.population, self.rng)
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
            return []
        selected = pareto_front(candidates, lambda g: candidate_estimates[g])
        proposals = [
            g
            for g in selected
            if not self.cache.record_proposal(
                g, experiment_type=self.experiment_type, protocol_version=self.protocol_version
            )
        ]
        if proposals:
            self.mixing_proposals += len(proposals)
            return proposals
        # Stall (same class of issue as P3Net's own module docstring,
        # simplification 2): every candidate this pass produced was
        # already fully evaluated -- inject fresh random diversity rather
        # than halting the run.
        fallback = self._random_valid_batch(1)
        self.mixing_proposals += len(fallback)
        return fallback
