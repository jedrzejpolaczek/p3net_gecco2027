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
import random
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import yaml
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation, Runner, RunState
from p3net.methods.p3net import P3Net
from sklearn.linear_model import LinearRegression

from methods import (
    SHEMOA,
    NSGANet,
    NSGANetV2,
    P3Absolute,
    P3Alone,
    RandomSearch,
    mo_bohb_method,
    tpe_method,
)
from search_spaces.nas_genotype import nas_search_space, nas_validity
from search_spaces.nas_hpo_bench_ii_genotype import (
    nas_hpo_bench_ii_search_space,
    nas_hpo_bench_ii_validity,
)
from stopping_rules import BudgetOrExplorationCollapse
from substrates.jahs_bench_201 import JAHSBench201Substrate
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
}

# substrate name (configs/search_spaces/*.yaml "substrate" field) ->
# (search_space_config) -> Substrate.
_SUBSTRATE_BUILDERS = {
    "jahs_bench_201": lambda cfg: JAHSBench201Substrate(dataset=cfg.get("dataset", "cifar10")),
    "nas_hpo_bench_ii": lambda cfg: NASHPOBenchIISubstrate(),
}


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


def build_substrate(search_space_config: dict[str, Any]):
    name = search_space_config["substrate"]
    try:
        builder = _SUBSTRATE_BUILDERS[name]
    except KeyError:
        raise ValueError(f"unknown substrate {name!r}") from None
    return builder(search_space_config)


def build_method(method_config: dict[str, Any], *, search_space, validity, rng, cache):
    """Method configs deliberately hold only YAML-serialisable data
    (population sizes, kappa, ...) -- model_factory is a Python callable
    supplied here, not sourced from the config file."""
    kind = method_config["method"]
    params = method_config.get("params", {})

    if kind == "p3net":
        return P3Net(
            search_space=search_space,
            validity=validity,
            model_factory=LinearRegression,
            rng=rng,
            cache=cache,
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
        return tpe_method(search_space, validity, cache=cache, **params)
    if kind == "mo_bohb":
        return mo_bohb_method(search_space, validity, rng, cache=cache, **params)
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


def run_single(
    method_config: dict[str, Any],
    search_space_config: dict[str, Any],
    budget: int,
    seed: int,
) -> RunResult:
    search_space, validity = build_search_space(search_space_config)
    substrate = build_substrate(search_space_config)
    rng = random.Random(seed)
    cache = EvaluationCache()
    method = build_method(
        method_config, search_space=search_space, validity=validity, rng=rng, cache=cache
    )
    runner = Runner(
        objective=substrate.objectives, budget=budget, stopping_rule=BudgetOrExplorationCollapse()
    )
    state = runner.run(method)
    return RunResult(state=state, cache=cache, method=method)


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
    return diagnostics


def persist_run(
    result: RunResult, *, method_name: str, search_space_name: str, budget: int, seed: int
) -> Path:
    out_path = result_path(
        method_name=method_name, search_space_name=search_space_name, budget=budget, seed=seed
    )
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
    out_path.write_text(json.dumps(payload, indent=2), encoding="utf-8")
    return out_path


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--method", required=True, help="configs/methods/<name>.yaml")
    parser.add_argument("--search-space", required=True, help="configs/search_spaces/<name>.yaml")
    parser.add_argument("--budget", type=int, required=True)
    parser.add_argument("--seed", type=int, required=True)
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
    )
    print(f"wrote {out_path} ({result.state.evaluations_used} evaluations)")


if __name__ == "__main__":
    main()
