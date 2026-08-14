"""Tree-structured Parzen Estimator (TPE) baseline (sanity check).

Unverified-against-live-data note: wraps the ask/tell scaffolding in
_ask_tell_shared.py. The real Optuna-based sampler/report is not wired up
yet (Stage C, ../../TASKS.md).
"""

from __future__ import annotations

from collections.abc import Callable

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import Objectives

from methods.external._ask_tell_shared import AskTellMethod


def tpe_method(
    sampler: Callable[[], Genotype],
    *,
    report: Callable[[Genotype, Objectives], None] | None = None,
    cache: EvaluationCache | None = None,
) -> AskTellMethod:
    return AskTellMethod(
        sampler=sampler,
        report=report,
        experiment_type="tpe",
        cache=cache if cache is not None else EvaluationCache(),
    )
