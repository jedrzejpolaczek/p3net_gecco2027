"""SH-EMOA baseline (multi-objective EA built on SMS-EMOA).

Unverified-against-live-data note: wraps the ask/tell scaffolding in
_ask_tell_shared.py. The real pymoo-based sampler/report -- translating
pymoo's SH-EMOA proposals to/from our Genotype/Objectives types -- is not
wired up yet (Stage C, ../../TASKS.md); construct with a `sampler`/`report`
pair matching AskTellMethod's protocol until then (e.g.
default_valid_sampler as a placeholder, as the tests do).
"""

from __future__ import annotations

from collections.abc import Callable

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import Objectives

from methods.external._ask_tell_shared import AskTellMethod


def sh_emoa_method(
    sampler: Callable[[], Genotype],
    *,
    report: Callable[[Genotype, Objectives], None] | None = None,
    cache: EvaluationCache | None = None,
) -> AskTellMethod:
    return AskTellMethod(
        sampler=sampler,
        report=report,
        experiment_type="sh_emoa",
        cache=cache if cache is not None else EvaluationCache(),
    )
