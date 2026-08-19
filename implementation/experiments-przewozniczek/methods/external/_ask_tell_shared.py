"""Shared ask/tell scaffolding for methods.external.{mo_bohb,tpe}.
Internal module, not re-exported.

Design note: MO-BOHB (hpbandster) and TPE (optuna) each have their own
real Python ask/tell API (optuna.Study.ask/tell,
hpbandster.optimizers.config_generators.bohb.BOHB.get_config/new_result).
`AskTellMethod` is the one thing both genuinely share once wired for
real: propose one genotype, evaluate it, report the result back --
dedup-cache integration and H_t bookkeeping live here once rather than
duplicated in mo_bohb.py and tpe.py, which each only need to supply a
real `sampler`/`report` pair (see their own modules for how those are
built from the real optuna/hpbandster APIs).
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import Objectives


@dataclass
class AskTellMethod:
    """Generic Method wrapping an external ask/tell optimiser. `sampler`
    proposes the next genotype to evaluate (translates a call into the
    real library's ask()); `report`, if given, is notified of every full
    evaluation (translates to the real library's tell()). Applies the
    same shared dedup cache as every other arm.
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
