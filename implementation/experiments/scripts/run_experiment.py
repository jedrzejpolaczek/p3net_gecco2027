"""
Entry point: run a single (method x benchmark x budget x seed) search.

Parses a method config (configs/methods/*.yaml -- for "p3net.yaml" this
configures p3net.methods.p3net directly; for every other file it
configures the corresponding methods/*.py arm) and a search-space config
(configs/search_spaces/*.yaml), instantiates the corresponding method
against the corresponding substrates/* adapter via p3net.harness.runner's
generic Runner (configured with stopping_rules.py's concrete StoppingRule)
for one seed, and persists the resulting H_t (raw per-run observation log)
under results/raw/.

Reference: chapters/v003/results/main.tex ("Experimental Setup" as a
whole).
"""

from __future__ import annotations

import argparse
import json
import math
import os
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, Runner, RunState
from p3net.methods.p3net import P3Net
from sklearn.linear_model import LinearRegression, RidgeCV

from measurement.resources import ResourceMeter, TimedSubstrate
from measurement.training_cost import simulated_training_seconds
from methods import (
    MOEAD,
    SHEMOA,
    MOLocalSearch,
    NSGANet,
    NSGANetV2,
    P3Absolute,
    P3Alone,
    RandomSearch,
    RegularizedEvolutionMO,
    botorch_method,
    mo_bohb_method,
    nsga3_method,
    smac_parego_method,
    tpe_method,
    vizier_method,
)
from methods.bananas_mo import BananasMO
from methods.bartnik_p3 import BartnikP3
from methods.multi_fidelity import AshaMO, BohbMO, HyperbandMO, MultiFidelityRunner
from methods.przewozniczek_p3elympus import PrzewozniczekP3ELyMPuS
from methods.reinforce_mo import ReinforceMO
from search_spaces.fcnet_genotype import fcnet_search_space, fcnet_validity
from search_spaces.nas_bench_201_genotype import (
    nas_bench_201_search_space,
    nas_bench_201_validity,
)
from search_spaces.nas_genotype import nas_search_space, nas_validity
from search_spaces.nas_hpo_bench_ii_genotype import (
    nas_hpo_bench_ii_search_space,
    nas_hpo_bench_ii_validity,
)
from stopping_rules import BudgetOrExplorationCollapse
from substrates.base import Substrate
from substrates.fcnet import FCNetSubstrate
from substrates.jahs_bench_201 import JAHSBench201Substrate
from substrates.nas_bench_201 import NASBench201Substrate
from substrates.nas_hpo_bench_ii import NASHPOBenchIISubstrate

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
CONFIGS_DIR = EXPERIMENTS_ROOT / "configs"
RESULTS_DIR = EXPERIMENTS_ROOT / "results" / "raw"

# search_space name (configs/search_spaces/*.yaml "search_space" field) ->
# () -> (SearchSpace, Validity). One entry per benchmark -- the two
# benchmarks do NOT share a genotype (search_spaces/nas_hpo_bench_ii_
# genotype.py's module docstring explains why); registry kept open for
# nsganetv2_continuous's separate representation once that lands.
_SEARCH_SPACE_BUILDERS = {
    "nas_genotype": lambda: (nas_search_space(), nas_validity),
    "nas_hpo_bench_ii_genotype": lambda: (
        nas_hpo_bench_ii_search_space(),
        nas_hpo_bench_ii_validity,
    ),
    "nas_bench_201_genotype": lambda: (nas_bench_201_search_space(), nas_bench_201_validity),
    "fcnet_genotype": lambda: (fcnet_search_space(), fcnet_validity),
}

# substrate name (configs/search_spaces/*.yaml "substrate" field) ->
# (search_space_config) -> Substrate.
_SUBSTRATE_BUILDERS = {
    "jahs_bench_201": lambda cfg: JAHSBench201Substrate(dataset=cfg.get("dataset", "cifar10")),
    "nas_hpo_bench_ii": lambda cfg: NASHPOBenchIISubstrate(),
    "nas_bench_201": lambda cfg: NASBench201Substrate(dataset=cfg.get("dataset", "cifar10")),
    "fcnet": lambda cfg: FCNetSubstrate(task=cfg["task"]),
}


_P3NET_SURROGATE_MODELS = {"ridge_cv": RidgeCV, "ols": LinearRegression}

_MULTI_FIDELITY_ARMS = {"hyperband_mo": HyperbandMO, "asha_mo": AshaMO, "bohb_mo": BohbMO}


#: kappa standing in for "no chain-depth cap" (the earlier kappa sweep's value).
KAPPA_UNBOUNDED = 1_000_000


def resolve_kappa(kappa: Any, *, n: int) -> int | None:
    """Symbolic kappa values in method configs, resolved per search space
    (n = genotype length): "log2n" = ceil(log2 n); "2log2n" = None, i.e.
    P3Net's own default 2 * ceil(log2 n); "unbounded" = KAPPA_UNBOUNDED.
    Integers and null pass through unchanged."""
    if kappa is None or isinstance(kappa, int):
        return kappa
    if kappa == "log2n":
        return math.ceil(math.log2(max(n, 2)))
    if kappa == "2log2n":
        return None
    if kappa == "unbounded":
        return KAPPA_UNBOUNDED
    raise ValueError(f"unknown kappa {kappa!r}")


def load_yaml(path: Path) -> dict[str, Any]:
    with path.open(encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def load_method_config(name: str) -> dict[str, Any]:
    return load_yaml(CONFIGS_DIR / "methods" / f"{name}.yaml")


def load_search_space_config(name: str) -> dict[str, Any]:
    return load_yaml(CONFIGS_DIR / "search_spaces" / f"{name}.yaml")


def load_budgets_config() -> dict[str, Any]:
    return load_yaml(CONFIGS_DIR / "experiment" / "budgets.yaml")


def build_search_space(search_space_config: dict[str, Any]):
    name = search_space_config["search_space"]
    try:
        builder = _SEARCH_SPACE_BUILDERS[name]
    except KeyError:
        raise ValueError(f"unknown search space {name!r}") from None
    return builder()


def build_substrate(search_space_config: dict[str, Any]) -> Substrate:
    name = search_space_config["substrate"]
    try:
        builder = _SUBSTRATE_BUILDERS[name]
    except KeyError:
        raise ValueError(f"unknown substrate {name!r}") from None
    return builder(search_space_config)


def build_method(
    method_config: dict[str, Any],
    *,
    search_space,
    validity,
    rng,
    cache,
    seed: int | None = None,
    substrate=None,
):
    """Method configs deliberately hold only YAML-serialisable data
    (population sizes, kappa, ...) -- model_factory is a Python callable
    supplied here, not sourced from the config file.

    `seed`, if given, is the same raw integer seed run_single built `rng`
    from (random.Random(seed)) -- passed through explicitly rather than
    reconstructed/guessed from `rng`, since `rng` alone can't be turned
    back into the int it came from. Only tpe/mo_bohb need it: every other
    method already replays deterministically end-to-end from `rng` alone
    (see methods/external/tpe.py, methods/external/mo_bohb.py module
    docstrings for why these two don't).

    `substrate` is likewise not YAML-serialisable and is only needed by
    the `p3net` branch below, to wire the substrate's own
    `analytic_cost_objectives` in as `methods.p3net.P3Net.analytic_cost`
    -- every other config ignores it."""
    kind = method_config["method"]
    params = dict(method_config.get("params", {}))

    if kind == "p3net":
        if substrate is None:
            raise ValueError("p3net config requires build_method to be given a substrate")
        # use_analytic_cost (default true): f2 computed fresh per candidate
        # during C* selection. false = the 2026-08-16 ablation's other arm,
        # f2 inherited from the ancestor (configs/methods/p3net_inherited_cost.yaml),
        # restored to re-validate that decision on the post-pyramid-fix engine.
        use_analytic_cost = params.pop("use_analytic_cost", True)
        # surrogate_model (default "ridge_cv"): "ols" = unregularised
        # LinearRegression, the model before RidgeCV was adopted on
        # 2026-08-18 -- selectable for the Design Evolution stages S1/S2.
        surrogate_model = params.pop("surrogate_model", "ridge_cv")
        if surrogate_model not in _P3NET_SURROGATE_MODELS:
            raise ValueError(f"unknown surrogate_model {surrogate_model!r}")
        params["kappa"] = resolve_kappa(params.get("kappa"), n=search_space.n)
        return P3Net(
            search_space=search_space,
            validity=validity,
            # RidgeCV, not LinearRegression: adopted 2026-08-18 (Results,
            # "Surrogate quality: magnitude calibration"; Conclusions) --
            # unregularised OLS produced wild, unstable predicted deltas
            # for a newly-matured pyramid level's first sweep pass
            # specifically (median squared error 6-19x every other level
            # size on real data). Regularisation strength is picked by
            # RidgeCV's own built-in cross-validation, not hand-tuned.
            model_factory=_P3NET_SURROGATE_MODELS[surrogate_model],
            rng=rng,
            cache=cache,
            analytic_cost=substrate.analytic_cost_objectives if use_analytic_cost else None,
            **params,
        )
    if kind == "p3_alone":
        return P3Alone(search_space=search_space, validity=validity, rng=rng, cache=cache, **params)
    if kind == "p3_absolute":
        return P3Absolute(
            search_space=search_space,
            validity=validity,
            model_factory=LinearRegression,
            rng=rng,
            cache=cache,
            **params,
        )
    if kind == "nsga_net":
        return NSGANet(search_space=search_space, validity=validity, rng=rng, cache=cache, **params)
    if kind == "nsganetv2":
        return NSGANetV2(
            search_space=search_space,
            validity=validity,
            model_factory=LinearRegression,
            rng=rng,
            cache=cache,
            **params,
        )
    if kind == "random_search":
        return RandomSearch(
            search_space=search_space, validity=validity, rng=rng, cache=cache, **params
        )
    if kind == "sh_emoa":
        return SHEMOA(search_space=search_space, validity=validity, rng=rng, cache=cache, **params)
    if kind == "tpe":
        return tpe_method(search_space, validity, cache=cache, seed=seed, **params)
    if kind == "mo_bohb":
        return mo_bohb_method(search_space, validity, rng, cache=cache, seed=seed, **params)
    if kind == "bartnik_p3":
        return BartnikP3(
            search_space=search_space, validity=validity, rng=rng, cache=cache, **params
        )
    if kind == "przewozniczek_p3elympus":
        return PrzewozniczekP3ELyMPuS(
            search_space=search_space, validity=validity, rng=rng, cache=cache, **params
        )
    if kind == "reinforce_mo":
        return ReinforceMO(
            search_space=search_space, validity=validity, rng=rng, cache=cache, **params
        )
    if kind == "bananas_mo":
        return BananasMO(
            search_space=search_space, validity=validity, rng=rng, cache=cache, **params
        )
    if kind == "mo_ls":
        return MOLocalSearch(
            search_space=search_space, validity=validity, rng=rng, cache=cache, **params
        )
    if kind == "regularized_evolution_mo":
        return RegularizedEvolutionMO(
            search_space=search_space, validity=validity, rng=rng, cache=cache, **params
        )
    if kind == "nsga3":
        return nsga3_method(search_space, validity, cache=cache, seed=seed, **params)
    if kind == "moead":
        return MOEAD(
            search_space=search_space,
            validity=validity,
            rng=rng,
            cache=cache,
            seed=seed or 0,
            **params,
        )
    if kind in ("botorch_qnehvi", "botorch_qparego"):
        return botorch_method(
            search_space,
            validity,
            rng,
            acquisition=kind.split("_", 1)[1],
            cache=cache,
            seed=seed,
            **params,
        )
    if kind == "smac3_parego":
        return smac_parego_method(search_space, validity, cache=cache, seed=seed, **params)
    if kind in _MULTI_FIDELITY_ARMS:
        if substrate is None:
            raise ValueError(f"{kind} config requires build_method to be given a substrate")
        return _MULTI_FIDELITY_ARMS[kind](
            search_space=search_space,
            validity=validity,
            rng=rng,
            cache=cache,
            full_epochs=substrate.max_epochs(),
            seed=seed or 0,
            **params,
        )
    if kind == "oss_vizier":
        return vizier_method(search_space, validity, cache=cache, seed=seed, **params)
    raise NotImplementedError(
        f"method {kind!r} is not runnable yet (configs/methods/{kind}.yaml is a "
        f"documented placeholder -- see its 'not_yet_implemented' note)"
    )


@dataclass(frozen=True)
class RunResult:
    """run_single's full output: the RunState reporting.* ultimately cares
    about, plus the cache and method instance it was produced with -- both
    needed to capture per-run diagnostics (duplication rate; P3-alone's
    sweeps_completed) that RunState itself has no reason to carry, since
    they're experiments-specific bookkeeping, not part of the library's
    generic harness contract."""

    state: RunState
    cache: EvaluationCache
    method: Any
    resources: dict[str, Any] | None = None


def run_single(
    method_config: dict[str, Any],
    search_space_config: dict[str, Any],
    budget: int,
    seed: int,
    *,
    substrate: Substrate | None = None,
) -> RunResult:
    """`substrate`, if given, is reused as-is instead of building a fresh
    one -- lets a caller running many points against the same benchmark
    (scripts/run_grid.py) share one Substrate instance (and, for
    JAHS-Bench-201, its one persistent subprocess bridge) across all of
    them, rather than paying that benchmark's setup cost per point."""
    search_space, validity = build_search_space(search_space_config)
    if substrate is None:
        substrate = build_substrate(search_space_config)
    timed = TimedSubstrate(substrate)
    rng = random.Random(seed)
    cache = EvaluationCache()
    with ResourceMeter(timed) as meter:
        method = build_method(
            method_config,
            search_space=search_space,
            validity=validity,
            rng=rng,
            cache=cache,
            seed=seed,
            substrate=timed,
        )
        if getattr(method, "multi_fidelity", False):
            # Multi-fidelity track: budget in full-evaluation equivalents
            # (methods/multi_fidelity.py, "Cost model").
            mf_runner = MultiFidelityRunner(substrate=timed, budget=budget)
            state = mf_runner.run(method)
            method.fidelity_queries = mf_runner.queries
            method.cost_used = mf_runner.cost_used
        else:
            runner = Runner(
                objective=timed.objectives,
                budget=budget,
                stopping_rule=BudgetOrExplorationCollapse(),
            )
            state = runner.run(method)
    resources = meter.as_dict()
    resources["device"] = getattr(method, "device", "cpu")
    resources["simulated_training_seconds"] = simulated_training_seconds(substrate, state, method)
    return RunResult(state=state, cache=cache, method=method, resources=resources)


def result_path(*, method_name: str, search_space_name: str, budget: int, seed: int) -> Path:
    return RESULTS_DIR / f"{method_name}__{search_space_name}__budget{budget}__seed{seed}.json"


def _observation_to_dict(obs: Observation) -> dict[str, Any]:
    return {"genotype": list(obs.genotype.values), "objectives": list(obs.objectives)}


def _diagnostics(result: RunResult) -> dict[str, Any]:
    """Per-run diagnostics reporting/*.py needs but RunState doesn't carry
    (see RunResult's docstring). Additive-only: readers of older raw JSON
    without a "diagnostics" key must still work (reporting/_common.py
    defaults it to {})."""
    diagnostics: dict[str, Any] = {"duplication_rate": result.cache.duplication_rate}
    sweeps_completed = getattr(result.method, "sweeps_completed", None)
    if sweeps_completed is not None:
        diagnostics["sweeps_completed"] = sweeps_completed
    surrogate_quality_log = getattr(result.method, "surrogate_quality_log", None)
    if surrogate_quality_log:
        diagnostics["surrogate_quality_log"] = [
            {"history_size": h, "predicted_delta": pd, "true_delta": td}
            for h, pd, td in surrogate_quality_log
        ]
    # Pyramid diagnostics (2026-08-17): promoted from ad-hoc instrumented
    # replay to first-class persisted fields (Results, "Diagnostics:
    # population-pyramid bootstrap share"). p3net and p3_absolute only --
    # both share p3net.search_engines.p3.pyramid.Pyramid since 2026-08-18
    # (Phase 3, Conclusions) -- absent (not zero) for every other method.
    bootstrap_proposals = getattr(result.method, "bootstrap_proposals", None)
    if bootstrap_proposals is not None:
        diagnostics["bootstrap_proposals"] = bootstrap_proposals
    mixing_proposals = getattr(result.method, "mixing_proposals", None)
    if mixing_proposals is not None:
        diagnostics["mixing_proposals"] = mixing_proposals
    surrogate_fit_seconds = getattr(result.method, "surrogate_fit_seconds", None)
    if surrogate_fit_seconds is not None:
        diagnostics["surrogate_fit_seconds"] = surrogate_fit_seconds
    linkage_tree_seconds = getattr(result.method, "linkage_tree_seconds", None)
    if linkage_tree_seconds is not None:
        diagnostics["linkage_tree_seconds"] = linkage_tree_seconds
    # chain_depth_log/level_size_log (2026-08-18): added specifically for
    # the magnitude-calibration follow-up investigation (Results,
    # "Surrogate quality: magnitude calibration") -- same order/length as
    # surrogate_quality_log, so a reader zips them back together by index.
    chain_depth_log = getattr(result.method, "chain_depth_log", None)
    if chain_depth_log:
        diagnostics["chain_depth_log"] = list(chain_depth_log)
    level_size_log = getattr(result.method, "level_size_log", None)
    if level_size_log:
        diagnostics["level_size_log"] = list(level_size_log)
    population_snapshots = getattr(result.method, "population_snapshots", None)
    if population_snapshots:
        # Same shape metrics.diagnostics.archive_turnover(archive_snapshots)
        # already expects and is already tested against -- persisted here,
        # turnover itself computed by reporting, not duplicated here.
        diagnostics["population_snapshots"] = [
            [list(genotype.values) for genotype in snapshot] for snapshot in population_snapshots
        ]
    if result.resources is not None:
        diagnostics["resources"] = result.resources
    decision_log = getattr(result.method, "decision_log", None)
    if decision_log is not None:
        diagnostics["surrogate_decisions"] = decision_log.as_dict()
    fidelity_queries = getattr(result.method, "fidelity_queries", None)
    if fidelity_queries is not None:
        diagnostics["cost_used"] = result.method.cost_used
        diagnostics["fidelity_queries"] = [
            {
                "genotype": list(q.genotype.values),
                "epochs": q.epochs,
                "objectives": list(q.objectives),
                "cost": q.cost,
            }
            for q in fidelity_queries
        ]
    return diagnostics


def persist_run(
    result: RunResult,
    *,
    method_name: str,
    search_space_name: str,
    budget: int,
    seed: int,
    out_dir: Path | None = None,
) -> Path:
    """Write one run's JSON atomically.

    The payload goes to a `.tmp` sibling first, is flushed and fsynced, and
    only then renamed onto the final name (`os.replace` is atomic on the
    same filesystem). A crash, kill, or power loss mid-write therefore
    leaves either no final file or a complete one -- never a truncated file
    that a resume check (`path.exists()`) would silently accept as done.

    `out_dir` defaults to results/raw/; scripts/run_pipeline.py passes its
    own per-commit run root instead."""
    if out_dir is None:
        out_path = result_path(
            method_name=method_name, search_space_name=search_space_name, budget=budget, seed=seed
        )
    else:
        out_path = out_dir / f"{method_name}__{search_space_name}__budget{budget}__seed{seed}.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "method": method_name,
        "search_space": search_space_name,
        "budget": budget,
        "seed": seed,
        "evaluations_used": result.state.evaluations_used,
        "history": [_observation_to_dict(obs) for obs in result.state.history],
        "diagnostics": _diagnostics(result),
    }
    tmp_path = out_path.with_name(out_path.name + ".tmp")
    with open(tmp_path, "w", encoding="utf-8") as handle:
        handle.write(json.dumps(payload, indent=2))
        handle.flush()
        os.fsync(handle.fileno())
    os.replace(tmp_path, out_path)
    return out_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", required=True, help="configs/methods/<name>.yaml")
    parser.add_argument("--search-space", required=True, help="configs/search_spaces/<name>.yaml")
    parser.add_argument("--budget", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
    parser.add_argument("--out-dir", type=Path, default=None, help="default: results/raw/")
    args = parser.parse_args(argv)

    method_config = load_method_config(args.method)
    search_space_config = load_search_space_config(args.search_space)
    result = run_single(method_config, search_space_config, args.budget, args.seed)
    out_path = persist_run(
        result,
        method_name=args.method,
        search_space_name=args.search_space,
        budget=args.budget,
        seed=args.seed,
        out_dir=args.out_dir,
    )
    print(f"wrote {out_path} ({result.state.evaluations_used} evaluations)")


if __name__ == "__main__":
    main()
