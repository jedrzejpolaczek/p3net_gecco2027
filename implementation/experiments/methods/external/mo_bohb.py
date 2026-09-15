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

Objective normalisation, fixed 2026-08-18 (Conclusions; CHANGELOG.md): the
random weight vector above was being multiplied directly against RAW
objectives, not ones brought to a comparable scale first. On
NAS-HPO-Bench-II specifically, f2 is roughly 19x f1's scale, so
max(weighted) was cost-dominated in the vast majority of calls regardless
of the drawn weight -- the "distribution of scalarised landscapes" this
mechanism exists to produce barely varied in the dimension that actually
matters. `_tchebycheff_scalarize` now min-max normalises by the running
per-objective range observed so far (updated in place on every call,
threaded through as `objective_mins`/`objective_maxs` rather than kept as
instance state, matching this module's existing closure-based style) --
this is what the reference implementation's own name, `tchebycheff_norm`,
already hinted was missing here, though the actual reference source is
unavailable to confirm the exact normalisation it uses (see above). This
change only affects `mo_bohb`'s own raw data; no other method is touched.
"""

from __future__ import annotations

import random
from collections.abc import Callable

import ConfigSpace as CS
import numpy as np
from hpbandster.core.dispatcher import Job
from hpbandster.optimizers.config_generators.bohb import BOHB as CG_BOHB
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives

from methods.external._ask_tell_shared import AskTellMethod

FIXED_BUDGET = 1.0


def _build_configspace(
    search_space: SearchSpace, *, seed: int | None = None
) -> CS.ConfigurationSpace:
    """`seed`, if given, seeds ConfigurationSpace's OWN internal
    numpy.random.RandomState (created fresh at construction time,
    independent of numpy's global RNG state -- confirmed by reading
    ConfigurationSpace.__init__/.seed in the installed ConfigSpace
    package). CG_BOHB.get_config falls back to
    self.configspace.sample_configuration() whenever no KDE model is
    fitted yet (and for a random_fraction of draws even once one is),
    so this configspace-level seed is required in addition to reseeding
    numpy's global state -- global-only reseeding was verified
    insufficient (still nondeterministic across instances)."""
    configspace = CS.ConfigurationSpace(seed=seed)
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
    objectives: Objectives,
    rng: random.Random,
    objective_mins: list[float],
    objective_maxs: list[float],
    *,
    rho: float = 0.05,
) -> float:
    """Randomly-weighted Tchebycheff scalarisation over objectives
    min-max normalised by the running per-objective range seen so far --
    see module docstring's "Objective normalisation" paragraph for why.
    Weights are non-negative and sum to 1.

    `objective_mins`/`objective_maxs` are mutated in place (updated here
    to always include this call's own `objectives` before normalising
    against them, so every call's own point is guaranteed within range)
    rather than carried as instance state, matching this module's
    existing closure-based style (mo_bohb_ask_tell's own
    `pending_configs`/`next_job_id`). A single-point range (or a
    genuinely constant objective) normalises to 0.0 rather than raising a
    division error."""
    if not objective_mins:
        objective_mins[:] = list(objectives)
        objective_maxs[:] = list(objectives)
    else:
        objective_mins[:] = [min(lo, o) for lo, o in zip(objective_mins, objectives)]
        objective_maxs[:] = [max(hi, o) for hi, o in zip(objective_maxs, objectives)]
    normalized = [
        (o - lo) / (hi - lo) if hi > lo else 0.0
        for o, lo, hi in zip(objectives, objective_mins, objective_maxs)
    ]
    raw_weights = [rng.random() + 1e-6 for _ in objectives]
    total = sum(raw_weights)
    weights = [w / total for w in raw_weights]
    weighted = [w * o for w, o in zip(weights, normalized)]
    return max(weighted) + rho * sum(weighted)


def mo_bohb_ask_tell(
    search_space: SearchSpace,
    validity: Validity,
    cache: EvaluationCache,
    *,
    rng: random.Random,
    top_n_percent: int = 15,
    min_points_in_model: int | None = None,
    seed: int | None = None,
    experiment_type: str = "mo_bohb",
    protocol_version: str = "v1",
) -> tuple[Callable[[], Genotype], Callable[[Genotype, Objectives], None]]:
    """Builds a real (sampler, report) pair backed by hpbandster's real
    BOHB config generator. `cache` must be the SAME EvaluationCache
    instance passed to the AskTellMethod this feeds. Calls
    cache.record_proposal (not the read-only cache.has) on every
    genotype the config generator suggests, duplicate or not, so the
    shared duplication instrumentation actually sees internally-retried
    duplicates instead of silently discarding them. AskTellMethod.
    propose's own outer record_proposal call, downstream of this one,
    then naturally becomes a no-op for whatever genotype this function
    returns (it can never be a duplicate by construction) -- counted
    twice as "seen" but never double-counted as a duplicate.

    `seed`, if given, reseeds numpy's GLOBAL random state right before
    constructing CG_BOHB: hpbandster's real BOHB config generator (see
    module docstring) has no per-instance seed/random_state parameter at
    all and draws its candidates via np.random.rand/randint/choice
    against whatever the global numpy RNG state happens to be. Reseeding
    here, at construction time rather than once at process start, is
    required for scripts/run_grid.py's single-process, multi-grid-point
    design to give each grid point (each with its own seed) independent,
    reproducible draws rather than a shared, order-dependent stream."""
    if seed is not None:
        np.random.seed(seed)
    configspace = _build_configspace(search_space, seed=seed)
    generator = CG_BOHB(
        configspace, top_n_percent=top_n_percent, min_points_in_model=min_points_in_model
    )
    pending_configs: dict[Genotype, dict] = {}
    next_job_id = 0
    # Running per-objective [min, max] for _tchebycheff_scalarize's own
    # normalisation (2026-08-18, module docstring) -- mutated in place by
    # that function, not reassigned here, so both closures below share
    # the same growing range.
    objective_mins: list[float] = []
    objective_maxs: list[float] = []

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
            if cache.record_proposal(
                genotype, experiment_type=experiment_type, protocol_version=protocol_version
            ):
                known = cache.get(
                    genotype, experiment_type=experiment_type, protocol_version=protocol_version
                )
                _tell_loss(
                    config, _tchebycheff_scalarize(known, rng, objective_mins, objective_maxs)
                )
                continue
            pending_configs[genotype] = config
            return genotype

    def report(genotype: Genotype, objectives: Objectives) -> None:
        config = pending_configs.pop(genotype)
        _tell_loss(config, _tchebycheff_scalarize(objectives, rng, objective_mins, objective_maxs))

    return sample, report


def mo_bohb_method(
    search_space: SearchSpace,
    validity: Validity,
    rng: random.Random,
    *,
    seed: int | None = None,
    cache: EvaluationCache | None = None,
) -> AskTellMethod:
    cache = cache if cache is not None else EvaluationCache()
    sampler, report = mo_bohb_ask_tell(
        search_space, validity, cache, rng=rng, seed=seed, experiment_type="mo_bohb"
    )
    return AskTellMethod(sampler=sampler, report=report, experiment_type="mo_bohb", cache=cache)
