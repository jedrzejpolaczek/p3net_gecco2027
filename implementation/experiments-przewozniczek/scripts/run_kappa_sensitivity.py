"""
Kappa / acceptance-threshold joint sensitivity sweep for P3Net
specifically.

P3Net's chain depth `kappa` and step-3 acceptance threshold are both
heuristic defaults (p3net.methods.p3net.P3Net's `kappa: int | None`,
resolved to eLyMPuS's own `2*ceil(log2(n))` bound if left null, and
`acceptance_threshold: float = 0.0`) whose sensitivity the paper commits
to assessing empirically rather than fixing by assumption. This module
runs that assessment: it resolves configs/experiment/
kappa_threshold_sweep.yaml's settled kappa x acceptance_threshold grid
against a real search space's actual genotype dimensionality `n`, runs
p3net (configs/methods/p3net.yaml as the base, kappa/acceptance_threshold
overridden per cell) once per (cell, seed), and reduces each cell's runs
into one `reporting.plots.SensitivityPoint` -- the exact shape
`reporting.plots.sensitivity_figure` consumes.

Why the settled kappa_threshold_sweep.yaml grid, not the four standalone
`configs/methods/p3net_kappa_*.yaml` / `p3net_threshold_*.yaml` ablation
configs directly: those four each vary exactly one axis relative to
p3net.yaml (useful as individually-identifiable, directly-runnable spot
checks via scripts/run_experiment.py -- results/raw/ keeps each one
separately), but a *joint* sensitivity grid (this module's job, and what
the paper's sensitivity paragraph and kappa_threshold_sweep.yaml's own
`swept_jointly: true` both call for) needs every kappa x threshold
combination, e.g. a "half kappa, strict threshold" cell that none of the
four single-axis configs alone produces.

Grid resolution: kappa_threshold_sweep.yaml's `kappa_grid` uses symbolic
entries ("auto_1x" = ceil(log2(n)), "auto_2x" = 2*ceil(log2(n)), null =
"infinity, no chain-depth cap") resolved here against the real search
space's `n` (mirrors p3net.methods.p3net.P3Net.__post_init__'s own
derivation, including its floor of n at 2). The `null` -> "infinity"
entry needs one documented adaptation: P3Net's own constructor treats
`kappa=None` as "use the eLyMPuS default" (2*ceil(log2(n))), NOT "no
cap" -- a real discrepancy between kappa_threshold_sweep.yaml's stated
intent and P3Net's actual runtime semantics for a null kappa. Since
p3net.py is not modified here, "infinity" is resolved to
KAPPA_UNBOUNDED_SENTINEL, a plain large int, instead of Python None --
large enough that P3Net's own `len(chain) >= self.kappa` force-break can
never trigger within any budget this project runs (<=350 full
evaluations; no single sweep's accepted-modification chain can plausibly
reach even a small fraction of the sentinel), functionally unbounded,
while still matching the constructor's literal `int` type.

Output shape: run_sensitivity_grid returns one SensitivityPoint per grid
cell, aggregating across the given seeds (median hypervolume, median
surrogate quality) the same way reporting/tables.py's fixed-budget
summary table aggregates per-seed scores into one row. hypervolume is
computed on a reference point shared across every cell/seed run in the
grid (reporting._common.nadir_reference_point over the pooled objectives
-- the same "one shared reference for everything being compared"
approach reporting/plots.py's convergence_curve_figure already uses),
so cells are comparable on the same scale. rank_correlation reuses
metrics.surrogate_quality.rank_correlation applied to each run's own
live (predicted_delta, true_delta) pairs
(p3net.methods.p3net.P3Net.surrogate_quality_log, the same live,
per-scoring-time signal scripts/run_experiment.py's diagnostics already
persist) -- a genuine Spearman rank correlation between the surrogate's
predicted and true deltas, not a repurposing of
metrics.surrogate_quality.pairwise_comparison_accuracy (the sign-
agreement metric reporting.surrogate_quality_figure uses instead): that
choice keeps SensitivityPoint's existing `rank_correlation` field
literally a rank correlation, computed from data delta_hat_F already
logs live, rather than renaming/repurposing the field. Cells whose runs
produced fewer than 2 scored predictions (e.g. a short budget that never
leaves the bootstrap phase) report `float("nan")` for that cell rather
than a fabricated value.

Every persisted-run byproduct (results/raw/p3net_kappa_sensitivity__
kappa<K>__threshold<T>__<search_space>__budget<B>__seed<S>.json, written
via scripts/run_experiment.persist_run under a synthetic method name
distinct from "p3net" and from the four standalone ablation configs, so
results/raw/ keeps every cell's raw H_t separately identifiable) is
optional (`persist=False` skips it) purely for cheap testing -- the real
CLI entry point always persists.

Reference: chapters/v003/proposed_optimizer/main.tex ("Chain depth
(kappa)"); chapters/v003/results/main.tex ("Surrogate error accumulation
(kappa and acceptance threshold)").
"""

from __future__ import annotations

import argparse
import math
import statistics
from collections.abc import Sequence
from typing import Any

from p3net.metrics import hypervolume
from p3net.problem.objectives import pareto_front

from metrics.surrogate_quality import rank_correlation
from reporting._common import nadir_reference_point
from reporting.plots import SensitivityPoint
from scripts.run_experiment import (
    CONFIGS_DIR,
    RunResult,
    build_search_space,
    build_substrate,
    load_method_config,
    load_search_space_config,
    load_yaml,
    persist_run,
    run_single,
)

SWEEP_CONFIG_PATH = CONFIGS_DIR / "experiment" / "kappa_threshold_sweep.yaml"

#: See module docstring's "Grid resolution" paragraph: a plain, large int
#: standing in for kappa_threshold_sweep.yaml's `null` ("infinity, no
#: chain-depth cap") grid entry, since P3Net's own constructor treats a
#: literal `None` kappa as "use the eLyMPuS default", not "no cap".
KAPPA_UNBOUNDED_SENTINEL = 10**6


def load_sweep_config() -> dict[str, Any]:
    """configs/experiment/kappa_threshold_sweep.yaml, as-is (symbolic
    entries unresolved) -- callers needing concrete values use
    resolve_kappa_grid/resolve_threshold_grid/sweep_cells below."""
    return load_yaml(SWEEP_CONFIG_PATH)


def resolve_kappa_grid(kappa_grid: Sequence[Any], *, n: int) -> list[int]:
    """Resolves kappa_threshold_sweep.yaml's `kappa_grid` entries (plain
    ints, "auto_1x", "auto_2x", or null) against a real search space's
    genotype dimensionality `n`. Mirrors p3net.methods.p3net.P3Net.
    __post_init__'s own default derivation exactly (including flooring n
    at 2), so "auto_2x" here always equals whatever `kappa: null` in
    configs/methods/p3net.yaml would itself resolve to at runtime for
    the same search space."""
    floored_n = max(n, 2)
    auto_1x = math.ceil(math.log2(floored_n))
    auto_2x = 2 * auto_1x
    resolved: list[int] = []
    for entry in kappa_grid:
        if entry is None:
            resolved.append(KAPPA_UNBOUNDED_SENTINEL)
        elif entry == "auto_1x":
            resolved.append(auto_1x)
        elif entry == "auto_2x":
            resolved.append(auto_2x)
        elif isinstance(entry, int):
            resolved.append(entry)
        else:
            raise ValueError(f"unknown kappa_grid entry {entry!r}")
    return resolved


def resolve_threshold_grid(threshold_grid: Sequence[Any], *, epsilon: float) -> list[float]:
    """Resolves kappa_threshold_sweep.yaml's `acceptance_threshold_grid`
    entries (plain floats, "epsilon", or "2*epsilon") against its own
    `epsilon` value."""
    resolved: list[float] = []
    for entry in threshold_grid:
        if entry == "epsilon":
            resolved.append(epsilon)
        elif entry == "2*epsilon":
            resolved.append(2 * epsilon)
        elif isinstance(entry, int | float):
            resolved.append(float(entry))
        else:
            raise ValueError(f"unknown acceptance_threshold_grid entry {entry!r}")
    return resolved


def sweep_cells(sweep_config: dict[str, Any], *, n: int) -> list[tuple[int, float]]:
    """Every (kappa, acceptance_threshold) cell of the resolved grid.
    Only `swept_jointly: true` (the full cross product) is implemented --
    kappa_threshold_sweep.yaml's own comment ("Swept JOINTLY (full cross
    product of both grids above)") documents no other sweep shape, so a
    `swept_jointly: false` config is a genuinely undefined request rather
    than one this function silently guesses an interpretation for."""
    if not sweep_config.get("swept_jointly", True):
        raise NotImplementedError(
            "sweep_cells only supports swept_jointly: true (the full cross product) -- "
            "configs/experiment/kappa_threshold_sweep.yaml documents no other sweep shape"
        )
    kappas = resolve_kappa_grid(sweep_config["kappa_grid"], n=n)
    thresholds = resolve_threshold_grid(
        sweep_config["acceptance_threshold_grid"], epsilon=sweep_config["epsilon"]
    )
    return [(kappa, threshold) for kappa in kappas for threshold in thresholds]


def _threshold_label(threshold: float) -> str:
    return f"{threshold}".replace(".", "p").replace("-", "neg")


def _cell_method_name(kappa: int, threshold: float) -> str:
    return f"p3net_kappa_sensitivity__kappa{kappa}__threshold{_threshold_label(threshold)}"


def _run_cell(
    *,
    base_params: dict[str, Any],
    kappa: int,
    threshold: float,
    search_space_config: dict[str, Any],
    budget: int,
    seeds: Sequence[int],
    substrate,
) -> list[RunResult]:
    method_config = {
        "method": "p3net",
        "params": {**base_params, "kappa": kappa, "acceptance_threshold": threshold},
    }
    return [
        run_single(method_config, search_space_config, budget, seed, substrate=substrate)
        for seed in seeds
    ]


def _cell_hypervolume(results: Sequence[RunResult], *, reference) -> float:
    values = []
    for result in results:
        objectives = [obs.objectives for obs in result.state.history]
        if not objectives:
            continue
        front = pareto_front(objectives, lambda p: p)
        values.append(hypervolume(front, reference))
    return statistics.median(values) if values else float("nan")


def _cell_rank_correlation(results: Sequence[RunResult]) -> float:
    per_seed: list[float] = []
    for result in results:
        log = getattr(result.method, "surrogate_quality_log", None) or []
        if len(log) < 2:
            continue
        predicted = [predicted_delta for _, predicted_delta, _ in log]
        true = [true_delta for _, _, true_delta in log]
        per_seed.append(rank_correlation(predicted, true))
    return statistics.median(per_seed) if per_seed else float("nan")


def run_sensitivity_grid(
    *,
    search_space_name: str,
    budget: int,
    seeds: Sequence[int],
    substrate=None,
    sweep_config: dict[str, Any] | None = None,
    base_method_config: dict[str, Any] | None = None,
    persist: bool = True,
) -> list[SensitivityPoint]:
    """Runs every (kappa, acceptance_threshold) x seed point of the
    resolved grid for one (search_space, budget), and reduces it to one
    SensitivityPoint per cell (median hypervolume / median surrogate rank
    correlation across seeds). `substrate`, if given, is reused as-is and
    never closed (caller owns it, same contract as
    scripts.run_experiment.run_single); otherwise one Substrate is built
    here and reused across the *entire* grid (every cell, every seed) --
    not rebuilt per cell -- and closed once the grid finishes, the same
    "one Substrate per benchmark, not per point" discipline
    scripts/run_grid.py already follows, for the same reason (JAHS-
    Bench-201's persistent-subprocess setup cost)."""
    search_space_config = load_search_space_config(search_space_name)
    search_space, _validity = build_search_space(search_space_config)
    n = search_space.n

    sweep_config = sweep_config if sweep_config is not None else load_sweep_config()
    base_method_config = (
        base_method_config if base_method_config is not None else load_method_config("p3net")
    )
    base_params = dict(base_method_config.get("params", {}))

    owns_substrate = substrate is None
    if substrate is None:
        substrate = build_substrate(search_space_config)

    try:
        cells = sweep_cells(sweep_config, n=n)
        results_by_cell: dict[tuple[int, float], list[RunResult]] = {}
        for kappa, threshold in cells:
            results = _run_cell(
                base_params=base_params,
                kappa=kappa,
                threshold=threshold,
                search_space_config=search_space_config,
                budget=budget,
                seeds=seeds,
                substrate=substrate,
            )
            results_by_cell[(kappa, threshold)] = results
            if persist:
                method_name = _cell_method_name(kappa, threshold)
                for seed, result in zip(seeds, results, strict=True):
                    persist_run(
                        result,
                        method_name=method_name,
                        search_space_name=search_space_name,
                        budget=budget,
                        seed=seed,
                    )

        all_points = [
            obs.objectives
            for results in results_by_cell.values()
            for result in results
            for obs in result.state.history
        ]
        reference = nadir_reference_point(all_points) if all_points else None

        points: list[SensitivityPoint] = []
        for (kappa, threshold), results in results_by_cell.items():
            hv = (
                _cell_hypervolume(results, reference=reference)
                if reference is not None
                else float("nan")
            )
            points.append(
                SensitivityPoint(
                    kappa=kappa,
                    acceptance_threshold=threshold,
                    hypervolume=hv,
                    rank_correlation=_cell_rank_correlation(results),
                )
            )
        return points
    finally:
        if owns_substrate:
            close = getattr(substrate, "close", None)
            if close is not None:
                close()


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--search-space", required=True, help="configs/search_spaces/<name>.yaml")
    parser.add_argument("--budget", type=int, required=True)
    parser.add_argument("--seeds", type=int, nargs="+", required=True)
    parser.add_argument(
        "--no-persist",
        action="store_true",
        help="don't write per-cell/seed raw JSON under results/raw/ (the grid still runs)",
    )
    args = parser.parse_args(argv)

    points = run_sensitivity_grid(
        search_space_name=args.search_space,
        budget=args.budget,
        seeds=args.seeds,
        persist=not args.no_persist,
    )
    for point in sorted(points, key=lambda p: (p.kappa, p.acceptance_threshold)):
        print(
            f"kappa={point.kappa} threshold={point.acceptance_threshold}: "
            f"hypervolume={point.hypervolume:.4f} rank_correlation={point.rank_correlation:.4f}"
        )


if __name__ == "__main__":
    main()
