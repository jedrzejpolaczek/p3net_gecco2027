"""P3Net: P3 engine + relative, linkage-aware surrogate delta_hat_F.

Known simplifications in this implementation, documented rather than
silently shipped:

1. **Single active level at a time, not full simultaneous cross-level
   cascading.** `search_engines/p3/pyramid.py`'s `Pyramid` IS wired in
   here (2026-08-15): population size is no longer a constructor
   argument -- level 0 starts at `growth_factor` individuals and a new,
   larger level is grown automatically once the current level's sweep
   passes stop improving (`Pyramid.all_stalled`), genuinely
   "parameter-less". What's still simplified relative to the canonical
   P3/GOMEA pyramid: only the newest level is actively swept at a time.
   Canonical P3 keeps every level live, cascading a single new solution's
   improvement attempt upward through all of them; here, once a level
   stalls and a new one is grown, the old level's population is frozen
   (its observations remain in H_t, but it is never swept again). A
   faithful multi-level-simultaneous cascade is a follow-up, not done
   here.
2. **f2 (analytic cost) is only freshly computed if the caller supplies
   `analytic_cost`.** Step 4's C* selection is supposed to use
   nondomination in (f_hat_1, f2), with f2 computed analytically per
   candidate without a full evaluation. The optional `analytic_cost`
   constructor argument (`Callable[[Genotype], Objectives]`) does exactly
   this when supplied: every objective other than f1 (index
   `objective_index`) is computed fresh for each candidate during C*
   selection. Left at its default (`None`), the previous approximation
   still applies -- every non-f1 objective is inherited from the
   ancestor's value rather than freshly computed -- correct and complete
   for single-objective use, and a documented, opt-in-to-fix
   simplification for multi-objective use rather than a silent gap.
3. **Stall recovery within one sweep pass is still random reinjection.**
   If a single sweep pass's C* ends up empty after dedup (every candidate
   that pass produced was already fully evaluated), this class falls
   back to proposing a small batch of fresh random valid genotypes for
   *that pass*, so the search keeps spending its budget rather than
   halting outright. This is a different, narrower situation than
   simplification 1's pyramid growth (which triggers on a pass
   completing without any real improvement, not on a pass producing zero
   *proposals*) -- both mechanisms coexist and do not conflict.
"""

from __future__ import annotations

import logging
import math
import random
from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Any

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives, dominates, pareto_front
from p3net.search_engines.p3.linkage_tree import build_linkage_tree, linkage_subsets
from p3net.search_engines.p3.optimal_mixing import SweepState
from p3net.search_engines.p3.pyramid import Pyramid, PyramidLevel
from p3net.surrogates.relative_linkage_aware import (
    NoLinkageTreeError,
    RelativeLinkageAwareSurrogate,
)
from p3net.surrogates.telescoping import AncestorNotEvaluatedError, ChainStep, telescoped_estimate

logger = logging.getLogger(__name__)


@dataclass
class P3Net:
    """P3Net: P3's optimal-mixing sweep scored by the relative,
    linkage-aware surrogate delta_hat_F, wired into the harness.Method
    protocol (propose/update) so it can be driven by harness.Runner.
    Operates exclusively at whatever single fidelity level the objective
    function passed to Runner represents -- the fidelity ladder is not
    consumed here.
    """

    search_space: SearchSpace
    validity: Validity
    model_factory: Callable[[], Any]
    rng: random.Random
    growth_factor: int = 2
    kappa: int | None = None
    acceptance_threshold: float = 0.0
    objective_index: int = 0
    analytic_cost: Callable[[Genotype], Objectives] | None = None
    experiment_type: str = "p3net"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    _pyramid: Pyramid = field(init=False, repr=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)

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
            self._pyramid.add_level()
        level = self._level
        if len(level.population) < level.size:
            return self._bootstrap_proposals(level)
        return self._sweep_proposals(level)

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        level = self._level
        level_index = self._level_index
        bootstrapping = len(level.population) < level.size

        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            self._history[obs.genotype] = obs

        if bootstrapping:
            # No established population to compare against yet -- fill
            # the level directly, no promote()/stall judgement (see
            # _seed_best_objectives below for how the baseline gets set
            # once bootstrap completes).
            for obs in new_observations:
                if obs.genotype not in level.population:
                    level.population.append(obs.genotype)
            if len(level.population) >= level.size:
                self._seed_best_objectives(level)
        else:
            # One promote() call per sweep pass (not per observation):
            # a pass's real outcome is its single best result, by Pareto
            # dominance -- calling promote() once per observation in a
            # mixed improve/non-improve batch would let a later
            # non-improving call overwrite an earlier improving one's
            # "not stalled" signal, incorrectly marking a genuinely
            # improving pass as stalled.
            best_obs = new_observations[0]
            for obs in new_observations[1:]:
                if dominates(obs.objectives, best_obs.objectives):
                    best_obs = obs
            self._pyramid.promote(level_index, best_obs.genotype, best_obs.objectives)
            for obs in new_observations:
                if obs.genotype not in level.population:
                    level.population.append(obs.genotype)

        if len(level.population) > level.size:
            level.population.sort(key=lambda g: self._history[g].objectives[self.objective_index])
            level.population = level.population[: level.size]

    # -- internals ---------------------------------------------------------

    def _seed_best_objectives(self, level: PyramidLevel) -> None:
        """Fold the just-completed bootstrap population down to its
        single best (by Pareto dominance) to give promote() a real
        baseline for the level's first post-bootstrap sweep pass --
        without this, that first pass would always count as "improving"
        simply because best_objectives was still None."""
        best: Genotype | None = None
        for g in level.population:
            obj = self._history[g].objectives
            if best is None or dominates(obj, self._history[best].objectives):
                best = g
        if best is not None:
            level.best_objectives = self._history[best].objectives

    def _bootstrap_proposals(self, level: PyramidLevel) -> list[Genotype]:
        """No linkage tree or surrogate can exist yet -- propose uniform
        random valid genotypes until this level reaches its target
        size."""
        needed = level.size - len(level.population)
        return self._diversity_injection(n=needed)

    def _sweep_proposals(self, level: PyramidLevel) -> list[Genotype]:
        # Step 6 (of the *previous* iteration): the tree and surrogate are
        # rebuilt once here, at the start of this iteration, and reused for
        # every parent's sweep below (steps 1-3) -- never rebuilt mid-sweep.
        linkage_root = build_linkage_tree(level.population)
        subsets = linkage_subsets(linkage_root)
        surrogate: RelativeLinkageAwareSurrogate | None = RelativeLinkageAwareSurrogate(
            model_factory=self.model_factory
        )
        try:
            surrogate.fit(
                list(self._history.values()), subsets, objective_index=self.objective_index
            )
        except NoLinkageTreeError:
            logger.debug(
                "not enough pairwise data to fit delta_hat_F this iteration "
                "(population=%d); proceeding without a surrogate",
                len(level.population),
            )
            surrogate = None

        # Steps 1-3: sweep every parent; candidate_estimates collects each
        # sweep's final individual and its (surrogate- or exactly-known)
        # estimated objectives, scoped to this iteration only.
        candidate_estimates: dict[Genotype, Objectives] = {}
        for parent in level.population:
            ancestor = self._history[parent]
            sweep = SweepState.start(parent, linkage_root, level.population, self.rng)
            chain: list[ChainStep] = []
            current_estimate: Objectives = ancestor.objectives
            while not sweep.done:
                proposal = sweep.propose()
                if not is_valid(proposal.candidate, self.validity):
                    sweep.reject(proposal)
                    continue
                trial_chain = chain + [
                    ChainStep(
                        x_prev=proposal.parent, x_next=proposal.candidate, subset=proposal.subset
                    )
                ]
                accept, trial_estimate = self._tentatively_accept(
                    surrogate, ancestor, trial_chain, proposal.candidate
                )
                if accept:
                    chain = trial_chain
                    sweep.accept(proposal)
                    current_estimate = trial_estimate
                    if len(chain) >= self.kappa:
                        break
                else:
                    sweep.reject(proposal)
            candidate_estimates[sweep.current] = current_estimate

        # Step 4: C* = candidates nondominated in this iteration's estimated
        # objective space only (not pooled across iterations).
        candidates = [g for g in candidate_estimates if is_valid(g, self.validity)]
        if not candidates:
            return []
        selected = pareto_front(candidates, lambda g: candidate_estimates[g])

        # Dedup: skip anything already in H_t / already proposed this run.
        proposals = [
            g
            for g in selected
            if not self.cache.record_proposal(
                g, experiment_type=self.experiment_type, protocol_version=self.protocol_version
            )
        ]
        if proposals:
            return proposals
        # Stall (module docstring, simplification 3): every candidate this
        # one sweep pass produced was already fully evaluated -- inject
        # fresh random diversity rather than halting the whole run. This
        # is a per-pass proposal-generation stall, distinct from
        # simplification 1's pyramid-growth trigger (which fires when a
        # *completed* pass yields no real improvement, not when a pass
        # yields zero proposals).
        return self._diversity_injection()

    def _diversity_injection(self, *, n: int = 1) -> list[Genotype]:
        proposals: list[Genotype] = []
        attempts = 0
        while len(proposals) < n and attempts < n * 50 + 50:
            attempts += 1
            candidate = self.search_space.sample_uniform(self.rng)
            if not is_valid(candidate, self.validity):
                continue
            if candidate in proposals:
                continue
            if self.cache.record_proposal(
                candidate,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            ):
                continue
            proposals.append(candidate)
        return proposals

    def _tentatively_accept(
        self,
        surrogate: RelativeLinkageAwareSurrogate | None,
        ancestor: Observation,
        chain: list[ChainStep],
        candidate: Genotype,
    ) -> tuple[bool, Objectives]:
        """Step 2-3: score a proposed chain via delta_hat_F, and tentatively
        accept iff it predicts nonnegative improvement (the configurable
        acceptance_threshold). ancestor is always drawn from H_t (the
        parent's own Observation), and the telescoping construction below
        enforces the x_0-in-H_t invariant itself.
        """
        if surrogate is None:
            # not enough data to score yet -- accept optimistically; the
            # real evaluation in step 5 corrects the record either way
            return True, ancestor.objectives
        try:
            estimate_f1 = telescoped_estimate(
                ancestor, chain, surrogate, set(self._history), objective_index=self.objective_index
            )
        except AncestorNotEvaluatedError:
            logger.warning(
                "telescoping ancestor %r was not in H_t -- this should never happen "
                "given the parent/x0-from-H_t invariant; accepting optimistically "
                "and continuing, but this indicates a real bug if it recurs",
                ancestor.genotype,
            )
            return True, ancestor.objectives
        predicted_improvement = ancestor.objectives[self.objective_index] - estimate_f1
        accept = predicted_improvement >= self.acceptance_threshold
        # Known simplification 2 (module docstring): non-f1 objectives are
        # freshly computed for `candidate` when analytic_cost is supplied,
        # otherwise inherited from the ancestor's value as before.
        non_f1_source = (
            self.analytic_cost(candidate) if self.analytic_cost is not None else ancestor.objectives
        )
        estimated_objectives = tuple(
            estimate_f1 if i == self.objective_index else non_f1_source[i]
            for i in range(len(ancestor.objectives))
        )
        return accept, estimated_objectives
