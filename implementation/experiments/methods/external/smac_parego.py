"""SMAC3 with ParEGO: random-forest Bayesian optimisation, multi-objective.

Why this arm: SMAC is a standard HPO baseline, and its random-forest
surrogate handles categorical inputs natively -- this project's genotype is
entirely categorical. ParEGO (random Chebyshev scalarisation per step) is
SMAC3's own multi-objective algorithm. It is a different surrogate family
from both the GP arms (qNEHVI, qParEGO) and the KDE arms (TPE, MO-BOHB).

Real: smac.HyperparameterOptimizationFacade driven through SMAC3's ask/tell
interface, with multi_objective_algorithm=smac.multi_objective.parego.ParEGO.
Every genotype coordinate is a ConfigSpace Categorical over that
coordinate's domain values. Everything else -- initial design, random
forest, acquisition function and its maximiser, intensifier -- is the
facade's default. Scenario is deterministic (both benchmarks are).

Handling shared with the other external arms:
  * an invalid genotype SMAC asks for is never evaluated. It is told back
    with the worst value of each objective observed so far among real
    evaluations (worst-case imputation), so SMAC learns to avoid it. It is
    NOT told as CRASHED with SMAC's default infinite crash cost: ParEGO
    normalises costs by their observed range, an infinite cost turns that
    into NaN, and SMAC's random forest then refuses to train (observed on
    NAS-HPO-Bench-II). Invalid trials asked before any real evaluation
    exists are held back and told as soon as the first one arrives;
  * a genotype already evaluated is told its real cached value, never
    re-evaluated;
  * SMAC's run-history files go to a per-run temporary directory.
"""

from __future__ import annotations

import logging
import tempfile
from collections.abc import Callable
from pathlib import Path

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives

from methods.external._ask_tell_shared import AskTellMethod


def _plain(value):
    """ConfigSpace hands back numpy scalars; genotypes hold plain Python values."""
    return value.item() if hasattr(value, "item") else value


def smac_parego_ask_tell(
    search_space: SearchSpace,
    validity: Validity,
    cache: EvaluationCache,
    *,
    seed: int,
    n_objectives: int = 2,
    experiment_type: str = "smac3_parego",
    protocol_version: str = "v1",
) -> tuple[
    Callable[[], Genotype], Callable[[Genotype, Objectives], None], tempfile.TemporaryDirectory
]:
    from ConfigSpace import Categorical, ConfigurationSpace
    from smac import HyperparameterOptimizationFacade, Scenario
    from smac.multi_objective.parego import ParEGO
    from smac.runhistory.dataclasses import TrialValue

    logging.getLogger("smac").setLevel(logging.ERROR)
    configspace = ConfigurationSpace(seed=seed)
    configspace.add(
        [Categorical(f"x{i}", list(domain.values)) for i, domain in enumerate(search_space.domains)]
    )
    workdir = tempfile.TemporaryDirectory(prefix="smac3_")
    scenario = Scenario(
        configspace,
        name=f"run_seed{seed}",
        output_directory=Path(workdir.name),
        deterministic=True,
        objectives=[f"f{j + 1}" for j in range(n_objectives)],
        n_trials=10**7,  # the harness budget, not SMAC, ends the run
        seed=seed,
    )
    smac = HyperparameterOptimizationFacade(
        scenario,
        target_function=lambda config, seed=0: [0.0] * n_objectives,  # never called: ask/tell only
        multi_objective_algorithm=ParEGO(scenario, seed=seed),
        overwrite=True,
        logging_level=logging.ERROR,
    )
    pending: dict[Genotype, object] = {}
    worst: list[float] | None = None
    deferred_invalid: list[object] = []

    def sample() -> Genotype:
        while True:
            info = smac.ask()
            config = info.config
            genotype = Genotype(
                values=tuple(_plain(config[f"x{i}"]) for i in range(search_space.n))
            )
            if not is_valid(genotype, validity):
                if worst is None:
                    deferred_invalid.append(info)
                else:
                    smac.tell(info, TrialValue(cost=list(worst)))
                continue
            if cache.record_proposal(
                genotype, experiment_type=experiment_type, protocol_version=protocol_version
            ):
                known = cache.get(
                    genotype, experiment_type=experiment_type, protocol_version=protocol_version
                )
                smac.tell(info, TrialValue(cost=list(known)))
                continue
            pending[genotype] = info
            return genotype

    def report(genotype: Genotype, objectives: Objectives) -> None:
        nonlocal worst
        smac.tell(pending.pop(genotype), TrialValue(cost=list(objectives)))
        worst = (
            list(objectives) if worst is None else [max(w, o) for w, o in zip(worst, objectives)]
        )
        while deferred_invalid:
            smac.tell(deferred_invalid.pop(0), TrialValue(cost=list(worst)))

    return sample, report, workdir


def smac_parego_method(
    search_space: SearchSpace,
    validity: Validity,
    *,
    seed: int | None = None,
    cache: EvaluationCache | None = None,
) -> AskTellMethod:
    cache = cache if cache is not None else EvaluationCache()
    sample, report, workdir = smac_parego_ask_tell(
        search_space, validity, cache, seed=seed if seed is not None else 0
    )
    method = AskTellMethod(
        sampler=sample, report=report, experiment_type="smac3_parego", cache=cache
    )
    method._workdir = workdir  # keeps SMAC's output directory alive exactly as long as the method
    return method
