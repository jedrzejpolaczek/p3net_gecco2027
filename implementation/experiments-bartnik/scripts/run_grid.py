"""
Sweep driver: full ablation grid (9 arms) + 5 extra baselines, both
benchmarks, all budget tiers, all seeds.

Enumerates every (method, search_space, budget, seed) combination from
configs/methods/*.yaml x configs/search_spaces/*.yaml x
configs/experiment/budgets.yaml, and dispatches each to
scripts/run_experiment.run_single (in-process, not a subprocess per
point). Skips combinations already persisted under results/raw/ rather
than re-running them. Methods whose config is marked
`not_yet_implemented: true` (e.g. nsganetv2_continuous) are excluded from
the default grid rather than left to fail at run_single time. A config
can also opt out of the default grid with `default_grid: false` without
being unimplemented -- for a runnable method that is a genuinely separate
analysis axis from the eleven-arm main comparison, where letting it into
results/raw/ alongside those arms would silently grow
reporting/tables.py's dynamically-derived baseline set and break the
paper's "ten/eleven arms" statistical scoping (reporting.
MAIN_COMPARISON_METHODS guards the report itself against this
independently). Both exclusions are defaults only, not hard blocks: pass
--methods explicitly to run any excluded config.

Points are run grouped by search_space, one Substrate instance built and
reused across every point that targets it (closed once that group is
done), rather than one fresh Substrate per point. This matters
specifically for JAHS-Bench-201: its Substrate holds a persistent
subprocess bridge that takes several minutes to load the surrogate
models on first query -- rebuilding it per point would pay that cost
once per grid point instead of once per benchmark. Both benchmarks are
deterministic (s=1 throughout), so sharing one Substrate's query cache
across every method/budget/seed that targets it changes nothing about
the results, only how many times that setup cost is paid. Each run still
gets its own fresh EvaluationCache (dedup / duplication-rate diagnostics
are unaffected by this grouping).

The CLI entry point prints a live, self-updating progress bar (points
done/total, elapsed time, rough ETA) by default -- disable with
--no-progress for a log-friendly (non-carriage-return) output stream.

Reference: chapters/v003/results/main.tex ("Baselines", Table
tab:ablation-grid, "Budgets, seeds, stopping").
"""

from __future__ import annotations

import argparse
import time
from collections import defaultdict
from dataclasses import dataclass
from pathlib import Path

from scripts.run_experiment import (
    CONFIGS_DIR,
    build_substrate,
    load_budgets_config,
    load_method_config,
    load_search_space_config,
    persist_run,
    result_path,
    run_single,
)


def _config_names(subdir: str) -> list[str]:
    return sorted(p.stem for p in (CONFIGS_DIR / subdir).glob("*.yaml"))


def _runnable_method_names() -> list[str]:
    return [
        name
        for name in _config_names("methods")
        if not load_method_config(name).get("not_yet_implemented", False)
        and load_method_config(name).get("default_grid", True)
    ]


def _runnable_search_space_names() -> list[str]:
    """Same `default_grid: false` opt-out as _runnable_method_names(),
    now for configs/search_spaces/*.yaml: a search space that is a
    genuinely separate analysis axis (e.g. nas_bench_201's architecture-only
    isolation experiment) stays out of the default grid without being
    unimplemented. Pass --search-spaces explicitly to run it anyway."""
    return [
        name
        for name in _config_names("search_spaces")
        if load_search_space_config(name).get("default_grid", True)
    ]


def _format_duration(seconds: float) -> str:
    seconds = max(0, int(seconds))
    hours, remainder = divmod(seconds, 3600)
    minutes, secs = divmod(remainder, 60)
    if hours:
        return f"{hours}h{minutes:02d}m{secs:02d}s"
    if minutes:
        return f"{minutes}m{secs:02d}s"
    return f"{secs}s"


def _print_progress(done: int, total: int, start_time: float, label: str) -> None:
    """One-line, carriage-return-updated progress bar -- lets a long
    scripts/run_grid.py invocation show it's still alive (rather than
    just silence between the occasional print) and roughly how much
    longer it has, without pulling in a third-party progress-bar
    dependency for something this simple."""
    elapsed = time.monotonic() - start_time
    fraction = done / total if total else 1.0
    bar_width = 24
    filled = int(bar_width * fraction)
    bar = "#" * filled + "-" * (bar_width - filled)
    eta = (elapsed / done) * (total - done) if done else 0.0
    print(
        f"\r[{bar}] {done}/{total} ({fraction:.0%}) "
        f"elapsed {_format_duration(elapsed)} eta {_format_duration(eta)} | {label}",
        end="",
        flush=True,
    )


@dataclass(frozen=True)
class GridPoint:
    method: str
    search_space: str
    budget: int
    seed: int


def enumerate_grid(
    *,
    methods: list[str] | None = None,
    search_spaces: list[str] | None = None,
    budgets: list[int] | None = None,
) -> list[GridPoint]:
    methods = methods if methods is not None else _runnable_method_names()
    search_spaces = search_spaces if search_spaces is not None else _runnable_search_space_names()
    budgets_config = load_budgets_config()
    tiers: list[int] = budgets if budgets is not None else budgets_config["budget_tiers"]
    seeds: list[int] = budgets_config["seeds"]
    return [
        GridPoint(method=method, search_space=space, budget=budget, seed=seed)
        for method in methods
        for space in search_spaces
        for budget in tiers
        for seed in seeds
    ]


def run_grid(
    points: list[GridPoint], *, skip_cached: bool = True, show_progress: bool = False
) -> tuple[list[Path], list[GridPoint]]:
    """Runs every grid point not already persisted under results/raw/,
    grouped by search_space so each benchmark's Substrate is built once
    and reused across every point in its group. Returns (paths written,
    points skipped as already cached). `show_progress` prints a one-line,
    self-updating progress bar (point count, elapsed time, rough ETA) to
    stdout as points complete -- off by default so library/test callers
    don't get console output they didn't ask for; `main()` turns it on
    for the CLI entry point."""
    written: list[Path] = []
    skipped: list[GridPoint] = []

    pending_by_space: dict[str, list[GridPoint]] = defaultdict(list)
    for point in points:
        out_path = result_path(
            method_name=point.method,
            search_space_name=point.search_space,
            budget=point.budget,
            seed=point.seed,
        )
        if skip_cached and out_path.exists():
            skipped.append(point)
            continue
        pending_by_space[point.search_space].append(point)

    total = sum(len(space_points) for space_points in pending_by_space.values())
    done = 0
    start_time = time.monotonic()

    for search_space_name, space_points in pending_by_space.items():
        search_space_config = load_search_space_config(search_space_name)
        if show_progress:
            _print_progress(done, total, start_time, f"building {search_space_name} substrate...")
        substrate = build_substrate(search_space_config)
        try:
            for point in space_points:
                if show_progress:
                    label = (
                        f"{point.method}/{point.search_space} "
                        f"budget={point.budget} seed={point.seed}"
                    )
                    _print_progress(done, total, start_time, label)
                method_config = load_method_config(point.method)
                result = run_single(
                    method_config,
                    search_space_config,
                    point.budget,
                    point.seed,
                    substrate=substrate,
                )
                written.append(
                    persist_run(
                        result,
                        method_name=point.method,
                        search_space_name=point.search_space,
                        budget=point.budget,
                        seed=point.seed,
                    )
                )
                done += 1
        finally:
            close = getattr(substrate, "close", None)
            if close is not None:
                close()

    if show_progress and total:
        _print_progress(done, total, start_time, "done")
        print()

    return written, skipped


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--methods", nargs="*", default=None, help="default: every runnable configs/methods/*.yaml"
    )
    parser.add_argument(
        "--search-spaces",
        nargs="*",
        default=None,
        help="default: every configs/search_spaces/*.yaml",
    )
    parser.add_argument(
        "--budgets",
        nargs="*",
        type=int,
        default=None,
        help="default: every tier in configs/experiment/budgets.yaml",
    )
    parser.add_argument(
        "--no-skip-cached", action="store_true", help="re-run points already on disk"
    )
    parser.add_argument("--no-progress", action="store_true", help="disable the live progress bar")
    args = parser.parse_args(argv)

    points = enumerate_grid(
        methods=args.methods, search_spaces=args.search_spaces, budgets=args.budgets
    )
    written, skipped = run_grid(
        points, skip_cached=not args.no_skip_cached, show_progress=not args.no_progress
    )
    print(
        f"ran {len(written)}/{len(points)} grid points ({len(skipped)} skipped as already cached)"
    )


if __name__ == "__main__":
    main()
