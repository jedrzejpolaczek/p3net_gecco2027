"""Shared ask/tell adapter scaffolding for methods.external.{sh_emoa,
mo_bohb,tpe}. Internal module, not re-exported.

Design note: SH-EMOA (pymoo), MO-BOHB (HpBandSter/Optuna), and TPE
(Optuna) each have their own real Python API, none of which is wired up
yet -- the packages aren't installed (Stage C in ../../TASKS.md). Rather
than guess at three different real APIs and risk building the wrong
shape, this scaffolding models the one thing all three genuinely share:
an ask/tell optimisation loop. `sampler` and `report` are the seam Stage C
replaces with real calls into each library; everything else (dedup cache,
genotype/H_t bookkeeping) is real, tested integration logic, not a
placeholder.
"""

from __future__ import annotations

import random
from collections.abc import Callable
from dataclasses import dataclass, field

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives


def default_valid_sampler(
    search_space: SearchSpace, validity: Validity, rng: random.Random
) -> Callable[[], Genotype]:
    """A simple rejection-sampling `sampler` callable: uniform random valid
    genotypes. Used as the Stage-B stand-in for a real library's ask() --
    Stage C replaces this with a sampler that actually queries pymoo /
    Optuna / HpBandSter and translates its proposal into a Genotype."""

    def sample() -> Genotype:
        while True:
            candidate = search_space.sample_uniform(rng)
            if is_valid(candidate, validity):
                return candidate

    return sample


@dataclass
class AskTellMethod:
    """Generic Method wrapping an external ask/tell optimiser. `sampler`
    proposes the next genotype to evaluate (Stage C: translates a call
    into the real library's ask()); `report`, if given, is notified of
    every full evaluation (Stage C: translates to the real library's
    tell()). Applies the same shared dedup cache as every other arm.
    """

    sampler: Callable[[], Genotype]
    report: Callable[[Genotype, Objectives], None] | None = None
    experiment_type: str = "external"
    protocol_version: str = "v1"
    cache: EvaluationCache = field(default_factory=EvaluationCache)

    def propose(self, state: RunState) -> list[Genotype]:
        attempts = 0
        while attempts < 200:
            attempts += 1
            candidate = self.sampler()
            if self.cache.record_proposal(
                candidate,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            ):
                continue
            return [candidate]
        return []

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(
                obs.genotype,
                obs.objectives,
                experiment_type=self.experiment_type,
                protocol_version=self.protocol_version,
            )
            if self.report is not None:
                self.report(obs.genotype, obs.objectives)
