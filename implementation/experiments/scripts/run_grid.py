"""
Sweep driver: full ablation grid (9 arms) + 5 extra baselines, both
benchmarks, all budget tiers, all seeds.

Enumerates every (method, search_space, budget, seed) combination from
configs/methods/*.yaml x configs/search_spaces/*.yaml x
configs/experiment/budgets.yaml, and dispatches each to
scripts/run_experiment.run_single (in-process, not a subprocess per
point). Skips combinations already persisted under results/raw/ rather
than re-running them.

Reference: chapters/v003/results/main.tex ("Baselines", Table
tab:ablation-grid, "Budgets, seeds, stopping").
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from pathlib import Path

from scripts.run_experiment import (
    CONFIGS_DIR,
    load_budgets_config,
    load_method_config,
    load_search_space_config,
    persist_run,
    result_path,
    run_single,
)


def _config_names(subdir: str) -> list[str]:
    return sorted(p.stem for p in (CONFIGS_DIR / subdir).glob("*.yaml"))


@dataclass(frozen=True)
class GridPoint:
    method: str
    search_space: str
    budget: int
    seed: int


def enumerate_grid(
    *, methods: list[str] | None = None, search_spaces: list[str] | None = None
) -> list[GridPoint]:
    methods = methods if methods is not None else _config_names("methods")
    search_spaces = search_spaces if search_spaces is not None else _config_names("search_spaces")
    budgets_config = load_budgets_config()
    tiers: list[int] = budgets_config["budget_tiers"]
    seeds: list[int] = budgets_config["seeds"]
    return [
        GridPoint(method=method, search_space=space, budget=budget, seed=seed)
        for method in methods
        for space in search_spaces
        for budget in tiers
        for seed in seeds
    ]


def run_grid(
    points: list[GridPoint], *, skip_cached: bool = True
) -> tuple[list[Path], list[GridPoint]]:
    """Runs every grid point not already persisted under results/raw/.
    Returns (paths written, points skipped as already cached)."""
    written: list[Path] = []
    skipped: list[GridPoint] = []
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
        method_config = load_method_config(point.method)
        search_space_config = load_search_space_config(point.search_space)
        state = run_single(method_config, search_space_config, point.budget, point.seed)
        written.append(
            persist_run(
                state,
                method_name=point.method,
                search_space_name=point.search_space,
                budget=point.budget,
                seed=point.seed,
            )
        )
    return written, skipped


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--methods", nargs="*", default=None, help="default: every configs/methods/*.yaml"
    )
    parser.add_argument(
        "--search-spaces",
        nargs="*",
        default=None,
        help="default: every configs/search_spaces/*.yaml",
    )
    parser.add_argument(
        "--no-skip-cached", action="store_true", help="re-run points already on disk"
    )
    args = parser.parse_args(argv)

    points = enumerate_grid(methods=args.methods, search_spaces=args.search_spaces)
    written, skipped = run_grid(points, skip_cached=not args.no_skip_cached)
    print(
        f"ran {len(written)}/{len(points)} grid points ({len(skipped)} skipped as already cached)"
    )


if __name__ == "__main__":
    main()
