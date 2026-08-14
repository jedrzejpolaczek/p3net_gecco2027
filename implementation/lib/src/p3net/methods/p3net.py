"""P3Net: P3 engine + relative, linkage-aware surrogate delta_hat_F.

Known simplifications in this implementation, documented rather than
silently shipped:

1. **Single population, not the full pyramid.** This runs the search loop
   (Proposed Optimizer, steps 1-6) over one fixed-size evolving
   population, rather than the full multi-level population pyramid
   (search_engines/p3/pyramid.py, implemented and unit-tested standalone
   but not yet wired in here). Population size is a constructor argument
   (`population_size`), not yet genuinely "parameter-less". Follow-up, not
   done here.
2. **f2 (analytic cost) is not freshly computed for unevaluated
   candidates.** Step 4's C* selection is supposed to use nondomination in
   (f_hat_1, f2), with f2 computed analytically per candidate without a
   full evaluation. This class has no analytic-cost hook yet, so any
   objective other than f1 (index `objective_index`) is approximated at
   its ancestor's value during C* selection rather than freshly computed
   for the candidate. Correct and complete for single-objective use;
   incomplete for genuine multi-objective (f1, f2) use until an
   analytic-cost callable is added. Follow-up, not done here.
3. **Stall recovery is simple random reinjection, not pyramid growth.** In
   the real P3 algorithm, a sweep converging with nothing left to accept
   is exactly what triggers growing a new, larger pyramid level (see
   simplification 1). Here, if an iteration's C* ends up empty after
   dedup (every candidate a sweep produced already fully evaluated), this
   class falls back to proposing a small batch of fresh random valid
   genotypes instead, so the search keeps spending its budget rather than
   stalling. A real pyramid-growth response is a follow-up.
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
from p3net.problem.objectives import Objectives, pareto_front
from p3net.search_engines.p3.linkage_tree import build_linkage_tree, linkage_subsets
from p3net.search_engines.p3.optimal_mixing import SweepState
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
    population_size: int = 20
    kappa: int | None = None
    acceptance_threshold: float = 0.0
    objective_index: int = 0
    experiment_type: str = "p3net"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    _population: list[Genotype] = field(default_factory=list, init=False, repr=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        if self.kappa is None:
            n = max(self.search_space.n, 2)
            self.kappa = 2 * math.ceil(math.log2(n))

    # -- harness.Method protocol ------------------------------------------

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

    # -- internals ---------------------------------------------------------

    def _bootstrap_proposals(self) -> list[Genotype]:
        """No linkage tree or surrogate can exist yet -- propose uniform
        random valid genotypes until the population reaches
        population_size."""
        needed = self.population_size - len(self._population)
        return self._diversity_injection(n=needed)

    def _sweep_proposals(self) -> list[Genotype]:
        # Step 6 (of the *previous* iteration): the tree and surrogate are
        # rebuilt once here, at the start of this iteration, and reused for
        # every parent's sweep below (steps 1-3) -- never rebuilt mid-sweep.
        linkage_root = build_linkage_tree(self._population)
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
                len(self._population),
            )
            surrogate = None

        # Steps 1-3: sweep every parent; candidate_estimates collects each
        # sweep's final individual and its (surrogate- or exactly-known)
        # estimated objectives, scoped to this iteration only.
        candidate_estimates: dict[Genotype, Objectives] = {}
        for parent in self._population:
            ancestor = self._history[parent]
            sweep = SweepState.start(parent, linkage_root, self._population, self.rng)
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
                accept, trial_estimate = self._tentatively_accept(surrogate, ancestor, trial_chain)
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
        # Stall: every candidate this sweep produced was already fully
        # evaluated (e.g. nothing was accepted anywhere, so every sweep's
        # `current` fell back to its already-known parent). Simplification
        # 3 (module docstring): inject fresh random diversity rather than
        # halting the whole run, since this class doesn't yet implement
        # the real algorithm's pyramid-growth response to a stalled sweep.
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
        estimated_objectives = tuple(
            estimate_f1 if i == self.objective_index else ancestor.objectives[i]
            for i in range(len(ancestor.objectives))
        )
        return accept, estimated_objectives
