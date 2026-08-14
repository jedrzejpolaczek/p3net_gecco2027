"""P3 alone (engine-only ablation, P3 side -- no surrogate)."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.search_engines.p3.linkage_tree import build_linkage_tree
from p3net.search_engines.p3.optimal_mixing import Proposal, SweepState

from methods._shared import random_valid_batch


@dataclass
class P3Alone:
    """P3's optimal-mixing sweep with NO surrogate: every proposed
    modification is gated by a REAL evaluation of f1 (canonical
    optimal-mixing acceptance rule -- accept iff the real f1 is no worse
    than the current individual's), exactly as in the original P3
    hill-climbing / cross-level mixing steps. Expected to exhaust most or
    all of a small budget within a handful of sweeps -- this is the point
    of the ablation, not a flaw (Results: motivates pairing P3 with a
    cheap surrogate in the first place). `sweeps_completed` tracks the
    diagnostic the paper asks for so a weak result reads as budget
    starvation, not engine failure.
    """

    search_space: SearchSpace
    validity: Validity
    rng: random.Random
    population_size: int = 10
    objective_index: int = 0
    experiment_type: str = "p3_alone"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    sweeps_completed: int = field(default=0, init=False)
    _population: list[Genotype] = field(default_factory=list, init=False, repr=False)
    _history: dict[Genotype, Observation] = field(default_factory=dict, init=False, repr=False)
    _current_sweep: SweepState | None = field(default=None, init=False, repr=False)
    _current_proposal: Proposal | None = field(default=None, init=False, repr=False)

    def propose(self, state: RunState) -> list[Genotype]:
        if len(self._population) < self.population_size:
            return self._bootstrap_one()

        for _ in range(20):  # try several sweeps in case some end with no new valid proposal at all
            if self._current_sweep is None or self._current_sweep.done:
                self._start_new_sweep()
            while not self._current_sweep.done:
                proposal = self._current_sweep.propose()
                if not is_valid(proposal.candidate, self.validity):
                    self._current_sweep.reject(proposal)
                    continue
                # Deduplication: a candidate already in H_t skips
                # reevaluation, but the sweep's acceptance decision is
                # still resolved from its cached true value -- dedup saves
                # the wasted evaluation, not the decision. record_proposal
                # also feeds the proposal-time duplication-rate diagnostic
                # for every candidate generated, hit or miss.
                is_duplicate = self.cache.record_proposal(
                    proposal.candidate,
                    experiment_type=self.experiment_type,
                    protocol_version=self.protocol_version,
                )
                if is_duplicate:
                    cached_objectives = self.cache.get(
                        proposal.candidate,
                        experiment_type=self.experiment_type,
                        protocol_version=self.protocol_version,
                    )
                    current_value = self._history[proposal.parent].objectives[self.objective_index]
                    if cached_objectives[self.objective_index] <= current_value:
                        self._current_sweep.accept(proposal)
                    else:
                        self._current_sweep.reject(proposal)
                    continue
                self._current_proposal = proposal
                return [proposal.candidate]
            self._finish_sweep()
        # Stall: 20 sweeps in a row produced nothing but duplicates -- fall
        # back to a fresh random valid genotype rather than halting the
        # run (same documented-fallback pattern as P3Net's stall recovery,
        # p3net.methods.p3net module docstring, simplification 3). Clear
        # _current_proposal so update() knows there is no sweep step to
        # resolve for this one -- it's a direct population replacement.
        self._current_proposal = None
        return self._bootstrap_one()

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            self._history[obs.genotype] = obs

            if len(self._population) < self.population_size:
                if obs.genotype not in self._population:
                    self._population.append(obs.genotype)
                continue

            if self._current_proposal is None:
                # Diversity-injection fallback (see propose()): no active
                # sweep proposal to resolve -- fold the new individual
                # into the population directly, replacing the current
                # worst performer.
                if obs.genotype not in self._population:
                    self._population.append(obs.genotype)
                    self._population.sort(
                        key=lambda g: self._history[g].objectives[self.objective_index]
                    )
                    self._population = self._population[: self.population_size]
                continue

            proposal = self._current_proposal
            current_value = self._history[proposal.parent].objectives[self.objective_index]
            if obs.objectives[self.objective_index] <= current_value:
                self._current_sweep.accept(proposal)
            else:
                self._current_sweep.reject(proposal)

            if self._current_sweep.done:
                self._finish_sweep()

    def _bootstrap_one(self) -> list[Genotype]:
        return random_valid_batch(
            1,
            self.search_space,
            self.validity,
            self.rng,
            self.cache,
            experiment_type=self.experiment_type,
            protocol_version=self.protocol_version,
        )

    def _start_new_sweep(self) -> None:
        linkage_root = build_linkage_tree(self._population)
        parent = self.rng.choice(self._population)
        self._current_sweep = SweepState.start(parent, linkage_root, self._population, self.rng)

    def _finish_sweep(self) -> None:
        self.sweeps_completed += 1
        final = self._current_sweep.current
        if final not in self._population:
            self._population.append(final)
            if len(self._population) > self.population_size:
                self._population.pop(0)
        self._current_sweep = None
