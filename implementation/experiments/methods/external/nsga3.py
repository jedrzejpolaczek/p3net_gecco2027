"""NSGA-III baseline (general-purpose MOEA, reference-point based).

Real: optuna.samplers.NSGAIIISampler driven through the same ask/tell
wrapper as TPE (methods.external.tpe.optuna_ask_tell), so invalid
genotypes, duplicates, and the shared deduplication cache are handled
identically to every other external arm.

Hyperparameters: optuna's library defaults (crossover, mutation,
reference points generated for two objectives), except population_size,
set to 20 to match every other population-based arm in this project
(NSGA-Net, NSGANetV2, SH-EMOA). No tuning -- baselines run at defaults
(paper, Limitations: tuning asymmetry).

Reference: Deb & Jain (2014), "An Evolutionary Many-Objective Optimization
Algorithm Using Reference-Point-Based Nondominated Sorting Approach".
"""

from __future__ import annotations

import optuna
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.problem.decoding import Validity
from p3net.problem.genotype import SearchSpace

from methods.external._ask_tell_shared import AskTellMethod
from methods.external.tpe import optuna_ask_tell


def nsga3_method(
    search_space: SearchSpace,
    validity: Validity,
    *,
    population_size: int = 20,
    n_objectives: int = 2,
    seed: int | None = None,
    cache: EvaluationCache | None = None,
) -> AskTellMethod:
    cache = cache if cache is not None else EvaluationCache()
    optuna.logging.set_verbosity(optuna.logging.WARNING)
    sampler, report = optuna_ask_tell(
        search_space,
        validity,
        cache,
        sampler=optuna.samplers.NSGAIIISampler(population_size=population_size, seed=seed),
        n_objectives=n_objectives,
        experiment_type="nsga3",
    )
    return AskTellMethod(sampler=sampler, report=report, experiment_type="nsga3", cache=cache)
