"""MO-BOHB baseline (Multi-Objective Bayesian Optimization Hyperband).

Real, but a documented adaptation rather than a faithful reproduction of
guerreroviu2021bagofbaselines's own MO-BOHB. Their reference code
(automl/multi-obj-baselines, baselines/methods/mobohb/) depends on a
custom-modified fork of hpbandster (its own vendored hpbandster/
subfolder, with a bespoke multi-objective config generator) that is not
published as an installable package -- only vanilla hpbandster is on
PyPI, and its real config generator
(hpbandster.optimizers.config_generators.bohb.BOHB) is fundamentally
single-objective: new_result() expects job.result["loss"] to be one
float (verified by reading its source directly, not guessed).

This module bridges that gap with random-weight Tchebycheff
scalarisation -- collapsing (f1, f2) into one scalar loss with a freshly
drawn random weight vector each time a result is reported, so the real
BOHB config generator's KDE model is fit against a distribution of
scalarised landscapes over the course of a run rather than one fixed
combination. This is the same technique visible in the reference
implementation's own MOBOHBWorker.tchebycheff_norm, applied here to the
REAL hpbandster.optimizers.config_generators.bohb.BOHB class rather than
their unpublished custom generator.

Fidelity-ladder usage, now resolved concretely: CG_BOHB.get_config(budget)
IS genuinely budget-aware (real Hyperband mechanics), but this project's harness
(p3net.harness.Runner / substrates.Substrate) only supports single-
fidelity (r_K) full evaluations, so this module always calls it with one
fixed budget value -- the same harness-level limitation already
documented for methods/sh_emoa.py's missing successive-halving half, not
a separate simplification invented here.
"""

from __future__ import annotations

import random
from collections.abc import Callable

import ConfigSpace as CS
from hpbandster.core.dispatcher import Job
from hpbandster.optimizers.config_generators.bohb import BOHB as CG_BOHB
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives

from methods.external._ask_tell_shared import AskTellMethod

FIXED_BUDGET = 1.0


def _build_configspace(search_space: SearchSpace) -> CS.ConfigurationSpace:
    configspace = CS.ConfigurationSpace()
    for i, domain in enumerate(search_space.domains):
        configspace.add(CS.CategoricalHyperparameter(f"x{i}", choices=list(domain.values)))
    return configspace


def _config_to_genotype(config: dict, search_space: SearchSpace) -> Genotype:
    """ConfigSpace hands back numpy scalar types (np.str_, np.float64,
    np.bool_), not the original Python objects -- match each coordinate
    back to its exact source value in the domain rather than blindly
    casting, so the resulting Genotype is identical in type to what
    every other arm produces (and stays JSON-serialisable for
    scripts/run_experiment.py's persist_run)."""
    values = []
    for i, domain in enumerate(search_space.domains):
        returned = config[f"x{i}"]
        values.append(next(original for original in domain.values if original == returned))
    return Genotype(values=tuple(values))


def _tchebycheff_scalarize(
    objectives: Objectives, rng: random.Random, *, rho: float = 0.05
) -> float:
    """Randomly-weighted Tchebycheff scalarisation -- see module
    docstring. Weights are non-negative and sum to 1."""
    raw_weights = [rng.random() + 1e-6 for _ in objectives]
    total = sum(raw_weights)
    weights = [w / total for w in raw_weights]
    weighted = [w * o for w, o in zip(weights, objectives)]
    return max(weighted) + rho * sum(weighted)


def mo_bohb_ask_tell(
    search_space: SearchSpace,
    validity: Validity,
    cache: EvaluationCache,
    *,
    rng: random.Random,
    top_n_percent: int = 15,
    min_points_in_model: int | None = None,
    experiment_type: str = "mo_bohb",
    protocol_version: str = "v1",
) -> tuple[Callable[[], Genotype], Callable[[Genotype, Objectives], None]]:
    """Builds a real (sampler, report) pair backed by hpbandster's real
    BOHB config generator. `cache` must be the SAME EvaluationCache
    instance passed to the AskTellMethod this feeds -- used here only
    for read lookups (cache.has/cache.get), never record_proposal, so
    AskTellMethod.propose stays the single place that counts proposals."""
    configspace = _build_configspace(search_space)
    generator = CG_BOHB(
        configspace, top_n_percent=top_n_percent, min_points_in_model=min_points_in_model
    )
    pending_configs: dict[Genotype, dict] = {}
    next_job_id = 0

    def _tell_loss(config: dict, loss: float) -> None:
        nonlocal next_job_id
        job = Job(next_job_id, budget=FIXED_BUDGET, config=config)
        next_job_id += 1
        job.result = {"loss": loss}
        generator.new_result(job)

    def sample() -> Genotype:
        while True:
            config, _info = generator.get_config(FIXED_BUDGET)
            genotype = _config_to_genotype(config, search_space)
            if not is_valid(genotype, validity):
                _tell_loss(config, float("inf"))
                continue
            if cache.has(
                genotype, experiment_type=experiment_type, protocol_version=protocol_version
            ):
                known = cache.get(
                    genotype, experiment_type=experiment_type, protocol_version=protocol_version
                )
                _tell_loss(config, _tchebycheff_scalarize(known, rng))
                continue
            pending_configs[genotype] = config
            return genotype

    def report(genotype: Genotype, objectives: Objectives) -> None:
        config = pending_configs.pop(genotype)
        _tell_loss(config, _tchebycheff_scalarize(objectives, rng))

    return sample, report


def mo_bohb_method(
    search_space: SearchSpace,
    validity: Validity,
    rng: random.Random,
    *,
    cache: EvaluationCache | None = None,
) -> AskTellMethod:
    cache = cache if cache is not None else EvaluationCache()
    sampler, report = mo_bohb_ask_tell(
        search_space, validity, cache, rng=rng, experiment_type="mo_bohb"
    )
    return AskTellMethod(sampler=sampler, report=report, experiment_type="mo_bohb", cache=cache)
