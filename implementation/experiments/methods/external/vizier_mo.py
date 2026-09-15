"""OSS Vizier: Google's default Bayesian-optimisation designer, multi-objective.

Why this arm: Vertex AI Vizier is the managed HPO service of a major cloud
provider; it cannot be run offline or reproducibly, but its algorithms are
published as OSS Vizier (Song et al., 2022, "Open Source Vizier:
Distributed Infrastructure and API for Reliable and Flexible Black-box
Optimization"). This arm stands in for the service.

Real: vizier._src.algorithms.designers.gp_ucb_pe.VizierGPUCBPEBandit, the
designer OSS Vizier's policy factory selects for algorithm "DEFAULT" (and
"GP_UCB_PE"). Every constructor argument is the library default except the
JAX random key, which is derived from the run seed. float64 is enabled, as
the Vizier service does. Multi-objective support
is the designer's own (both metrics declared MINIMIZE in the problem
statement); nothing is scalarised here.

Search space: every genotype coordinate is a Vizier CATEGORICAL parameter
over that coordinate's domain values. Vizier categorical values are
strings, so each value is represented by its position in the domain
("0", "1", ...) and mapped back on suggestion -- a bijection, so the
designer sees exactly the genotype's categories.

Handling shared with the other external arms:
  * an invalid genotype the designer suggests is never evaluated. It is
    completed as infeasible (Vizier's own mechanism for failed trials,
    `infeasibility_reason`), so no objective value is invented for it;
  * a genotype already evaluated is completed with its real cached value,
    never re-evaluated;
  * one suggestion is requested per step (count=1).
"""

from __future__ import annotations

from collections.abc import Callable

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives

from methods.external._ask_tell_shared import AskTellMethod


def vizier_ask_tell(
    search_space: SearchSpace,
    validity: Validity,
    cache: EvaluationCache,
    *,
    seed: int,
    n_objectives: int = 2,
    experiment_type: str = "oss_vizier",
    protocol_version: str = "v1",
) -> tuple[Callable[[], Genotype], Callable[[Genotype, Objectives], None]]:
    import jax
    from vizier import algorithms as vza
    from vizier._src.algorithms.designers.gp_ucb_pe import VizierGPUCBPEBandit
    from vizier.service import pyvizier as vz

    problem = vz.ProblemStatement()
    root = problem.search_space.root
    for i, domain in enumerate(search_space.domains):
        root.add_categorical_param(f"x{i}", [str(k) for k in range(len(domain.values))])
    for j in range(n_objectives):
        problem.metric_information.append(
            vz.MetricInformation(name=f"f{j + 1}", goal=vz.ObjectiveMetricGoal.MINIMIZE)
        )
    # The Vizier service enables float64 before running any designer
    # (vizier/_src/service/pythia_service.py); do the same so the GP runs as
    # it does in the service. JAX is used by no other arm in this process.
    jax.config.update("jax_enable_x64", True)
    designer = VizierGPUCBPEBandit(problem, rng=jax.random.PRNGKey(seed))

    pending: dict[Genotype, vz.Trial] = {}
    next_id = 1

    def complete(trial: vz.Trial, measurement: vz.Measurement | None, reason: str | None) -> None:
        trial.complete(measurement or vz.Measurement(), infeasibility_reason=reason)
        designer.update(vza.CompletedTrials([trial]), vza.ActiveTrials())

    def measurement(objectives: Objectives) -> vz.Measurement:
        return vz.Measurement(metrics={f"f{j + 1}": float(v) for j, v in enumerate(objectives)})

    def sample() -> Genotype:
        nonlocal next_id
        while True:
            suggestion = designer.suggest(count=1)[0]
            trial = suggestion.to_trial(next_id)
            next_id += 1
            genotype = Genotype(
                values=tuple(
                    domain.values[int(trial.parameters[f"x{i}"].value)]
                    for i, domain in enumerate(search_space.domains)
                )
            )
            if not is_valid(genotype, validity):
                complete(trial, None, "invalid genotype")
                continue
            if cache.record_proposal(
                genotype, experiment_type=experiment_type, protocol_version=protocol_version
            ):
                known = cache.get(
                    genotype, experiment_type=experiment_type, protocol_version=protocol_version
                )
                complete(trial, measurement(known), None)
                continue
            pending[genotype] = trial
            return genotype

    def report(genotype: Genotype, objectives: Objectives) -> None:
        complete(pending.pop(genotype), measurement(objectives), None)

    return sample, report


def vizier_method(
    search_space: SearchSpace,
    validity: Validity,
    *,
    seed: int | None = None,
    cache: EvaluationCache | None = None,
) -> AskTellMethod:
    cache = cache if cache is not None else EvaluationCache()
    sample, report = vizier_ask_tell(
        search_space, validity, cache, seed=seed if seed is not None else 0
    )
    return AskTellMethod(sampler=sample, report=report, experiment_type="oss_vizier", cache=cache)
