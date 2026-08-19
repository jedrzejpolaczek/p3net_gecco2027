"""Tree-structured Parzen Estimator (TPE) baseline (sanity check).

Real: wraps optuna.samplers.TPESampler via optuna's ask/tell API
(study.ask()/study.tell()) rather than optuna.Study.optimize()'s callback
style, since this project drives every arm through the shared
p3net.harness.Runner (propose one genotype, evaluate it, report back),
not the other way around. optuna's TPESampler supports multi-objective
studies natively (used here since every arm here is compared on
(f1, f2)), so no separate single/multi-objective code path is needed.

Every optuna trial this module asks for is eventually told something
real, never fabricated -- exactly the three cases below, no others:
- invalid (fails this project's Validity check): told FAILED
- a duplicate of an already-evaluated genotype: told its REAL cached
  value (a genuine value, just not from a fresh evaluation)
- a genuinely new, valid, not-yet-seen genotype: returned to the
  harness for a real evaluation, told that real result once it's back
Leaving a trial permanently un-told (e.g. quietly discarding a duplicate)
would leak optuna-internal state and bias TPESampler's model with
trials it thinks are still pending.
"""

from __future__ import annotations

from collections.abc import Callable

import optuna
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives

from methods.external._ask_tell_shared import AskTellMethod


def _suggest_genotype(trial: optuna.trial.Trial, search_space: SearchSpace) -> Genotype:
    values = tuple(
        trial.suggest_categorical(f"x{i}", list(domain.values))
        for i, domain in enumerate(search_space.domains)
    )
    return Genotype(values=values)


def tpe_ask_tell(
    search_space: SearchSpace,
    validity: Validity,
    cache: EvaluationCache,
    *,
    n_objectives: int = 2,
    seed: int | None = None,
    experiment_type: str = "tpe",
    protocol_version: str = "v1",
) -> tuple[Callable[[], Genotype], Callable[[Genotype, Objectives], None]]:
    """Builds a real (sampler, report) pair backed by optuna's TPESampler.
    `cache` must be the SAME EvaluationCache instance passed to the
    AskTellMethod this feeds. Calls cache.record_proposal (not the
    read-only cache.has) on every genotype optuna suggests, duplicate or
    not, so the shared duplication instrumentation actually sees
    internally-retried duplicates instead of silently discarding them.
    AskTellMethod.propose's own outer record_proposal call, downstream of
    this one, then naturally becomes a no-op for whatever genotype this
    function returns (it can never be a duplicate by construction) --
    counted twice as "seen" but never double-counted as a duplicate."""
    study = optuna.create_study(
        directions=["minimize"] * n_objectives,
        sampler=optuna.samplers.TPESampler(seed=seed),
    )
    pending_trials: dict[Genotype, optuna.trial.Trial] = {}

    def sample() -> Genotype:
        while True:
            trial = study.ask()
            genotype = _suggest_genotype(trial, search_space)
            if not is_valid(genotype, validity):
                study.tell(trial, state=optuna.trial.TrialState.FAIL)
                continue
            if cache.record_proposal(
                genotype, experiment_type=experiment_type, protocol_version=protocol_version
            ):
                known = cache.get(
                    genotype, experiment_type=experiment_type, protocol_version=protocol_version
                )
                study.tell(trial, values=list(known))
                continue
            pending_trials[genotype] = trial
            return genotype

    def report(genotype: Genotype, objectives: Objectives) -> None:
        trial = pending_trials.pop(genotype)
        study.tell(trial, values=list(objectives))

    return sample, report


def tpe_method(
    search_space: SearchSpace,
    validity: Validity,
    *,
    n_objectives: int = 2,
    seed: int | None = None,
    cache: EvaluationCache | None = None,
) -> AskTellMethod:
    cache = cache if cache is not None else EvaluationCache()
    sampler, report = tpe_ask_tell(
        search_space, validity, cache, n_objectives=n_objectives, seed=seed, experiment_type="tpe"
    )
    return AskTellMethod(sampler=sampler, report=report, experiment_type="tpe", cache=cache)
