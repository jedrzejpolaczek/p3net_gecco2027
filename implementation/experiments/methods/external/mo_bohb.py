"""MO-BOHB baseline (Multi-Objective Bayesian Optimization Hyperband).

Unverified-against-live-data note: wraps the ask/tell scaffolding in
_ask_tell_shared.py. The real HpBandSter/Optuna-based sampler/report is
not wired up yet (Stage C, ../../TASKS.md). Also open, per that TASKS.md
entry: whether/how this arm is allowed to consume p3net.problem's generic
fidelity ladder -- Hyperband is naturally fidelity-aware, unlike every
other arm in the main comparison (which operates only at r_K) -- to be
decided explicitly once the real backend is wired up, not left implicit.
"""

from __future__ import annotations

from collections.abc import Callable

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import Objectives

from methods.external._ask_tell_shared import AskTellMethod


def mo_bohb_method(
    sampler: Callable[[], Genotype],
    *,
    report: Callable[[Genotype, Objectives], None] | None = None,
    cache: EvaluationCache | None = None,
) -> AskTellMethod:
    return AskTellMethod(
        sampler=sampler,
        report=report,
        experiment_type="mo_bohb",
        cache=cache if cache is not None else EvaluationCache(),
    )
