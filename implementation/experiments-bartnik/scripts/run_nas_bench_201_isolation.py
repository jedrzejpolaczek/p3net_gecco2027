"""
Single entry point for the architecture-only NAS-Bench-201 isolation
experiment (glimmering-swimming-book.md, Faza 4): smoke test -> full grid
run -> statistical analysis, so a single invocation covers the whole
pipeline instead of three manual steps.

Tests P3Net vs random_search on nas_bench_201 (architecture-only, no
Theta) -- the direct test of whether this project's own joint
architecture+hyperparameter genotype extension explains P3Net's failure
to separate from random_search on both joint benchmarks
(chapters/v003/conclusions/main.tex, "Why the results are what they
are").

Aborts before the (expensive) grid run if the smoke test fails, so a
broken environment (missing data/cache/nats_bench/, a substrate
regression) fails fast rather than after minutes of real queries.

Usage (from implementation/experiments):
    uv run python scripts/run_nas_bench_201_isolation.py

Writes results/nas_bench_201_isolation_result.md with the Wilcoxon +
Holm-Bonferroni + Cliff's delta result for each budget tested -- the
exact analysis a human would otherwise have to request separately.
"""

from __future__ import annotations

import sys
from pathlib import Path

from p3net.metrics import hypervolume_relative_to_best_known_front
from p3net.problem.objectives import pareto_front

from reporting._common import construct_best_known_front, load_raw_run, nadir_reference_point
from scripts.run_experiment import load_method_config, load_search_space_config, run_single
from scripts.run_grid import enumerate_grid, run_grid
from stats.significance import Comparison, compare_p3net_to_baselines

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = EXPERIMENTS_ROOT / "results" / "raw"
OUTPUT_PATH = EXPERIMENTS_ROOT / "results" / "nas_bench_201_isolation_result.md"

SEARCH_SPACE = "nas_bench_201"
METHODS = ("p3net", "random_search")
BUDGETS = (100, 350)


def smoke_test() -> bool:
    """One tiny, real-data run confirming the whole path (config -> search
    space -> substrate -> real nats_bench query -> result) works before
    committing to the full grid. Returns False (never raises) on any
    failure, so main() can decide whether to proceed."""
    print("Running smoke test (budget=5, random_search, nas_bench_201)...")
    try:
        result = run_single(
            load_method_config("random_search"), load_search_space_config(SEARCH_SPACE), budget=5, seed=1
        )
    except Exception as exc:  # noqa: BLE001 -- deliberately broad: any failure here means "don't proceed"
        print(f"SMOKE TEST FAILED: {exc!r}")
        return False

    if result.state.evaluations_used != 5:
        print(f"SMOKE TEST FAILED: expected 5 evaluations, got {result.state.evaluations_used}")
        return False

    f1, f2 = result.state.history[-1].objectives
    if not (0.0 <= f1 <= 100.0):
        print(f"SMOKE TEST FAILED: implausible error rate f1={f1}")
        return False
    if not (f2 > 0.0):
        print(f"SMOKE TEST FAILED: implausible FLOPs f2={f2}")
        return False

    print(f"SMOKE TEST PASSED (f1={f1:.2f}, f2={f2:.2f})")
    return True


def run_full_grid() -> None:
    """R=30 seeds x 2 budgets x 2 methods = 120 real-data points, skipping
    anything already persisted under results/raw/ (so a re-run after an
    interruption only fills in what's missing)."""
    points = enumerate_grid(methods=list(METHODS), search_spaces=[SEARCH_SPACE], budgets=list(BUDGETS))
    written, skipped = run_grid(points, skip_cached=True, show_progress=True)
    print(f"ran {len(written)}/{len(points)} grid points ({len(skipped)} already cached)")


def analyze() -> str:
    """Wilcoxon signed-rank + Holm-Bonferroni + Cliff's delta, p3net vs
    random_search, per budget -- the same stats/significance.py machinery
    the main comparison grid uses, scoped to just this one baseline pair
    and search space."""
    # Scoped glob, not load_raw_runs(RESULTS_DIR): results/raw/ holds
    # 15000+ files across the whole project's main grid by this point --
    # loading every one just to filter down to this one search space would
    # be minutes of wasted JSON parsing. result_path()'s own naming
    # convention ({method}__{search_space}__budget{budget}__seed{seed}.json)
    # makes the scoped glob exact, not a guess.
    runs = [
        load_raw_run(path)
        for method in METHODS
        for path in RESULTS_DIR.glob(f"{method}__{SEARCH_SPACE}__*.json")
    ]
    if not runs:
        raise RuntimeError(f"no {SEARCH_SPACE} raw runs found under {RESULTS_DIR} -- did the grid run complete?")

    best_known = construct_best_known_front(runs)
    all_points = [p for r in runs for p in r.objectives]
    reference = nadir_reference_point(all_points)

    def scores_by_seed(method: str, budget: int) -> dict[int, float]:
        return {
            r.seed: hypervolume_relative_to_best_known_front(
                pareto_front(list(r.objectives), lambda p: p), best_known, reference
            )
            for r in runs
            if r.method == method and r.budget == budget
        }

    comparisons = []
    for budget in BUDGETS:
        p3net_scores = scores_by_seed("p3net", budget)
        rs_scores = scores_by_seed("random_search", budget)
        shared_seeds = sorted(set(p3net_scores) & set(rs_scores))
        if len(shared_seeds) < 2:
            print(f"budget={budget}: skipped, only {len(shared_seeds)} paired seed(s) available")
            continue
        comparisons.append(
            Comparison(
                baseline="random_search",
                benchmark=SEARCH_SPACE,
                budget=budget,
                p3net_scores=tuple(p3net_scores[s] for s in shared_seeds),
                baseline_scores=tuple(rs_scores[s] for s in shared_seeds),
            )
        )

    results = compare_p3net_to_baselines(comparisons)

    lines = [
        "# NAS-Bench-201 isolation experiment: p3net vs random_search",
        "",
        "Architecture-only NAS-Bench-201 (no Theta), testing whether removing this project's own joint "
        "architecture+hyperparameter genotype extension lets P3Net separate from random_search where it "
        "does not on the two joint benchmarks (conclusions/main.tex, \"Why the results are what they are\").",
        "",
        "| Budget | n | Median p3net | Median random_search | Adj. p | Cliff's delta | Reject H0 |",
        "|---|---|---|---|---|---|---|",
    ]
    import statistics

    for result in results:
        c = result.comparison
        lines.append(
            f"| {c.budget} | {len(c.p3net_scores)} | {statistics.median(c.p3net_scores):.4f} | "
            f"{statistics.median(c.baseline_scores):.4f} | {result.adjusted_p_value:.4f} | "
            f"{result.effect_size:+.3f} | {result.reject_null} |"
        )

    output = "\n".join(lines) + "\n"
    print("\n" + output)
    OUTPUT_PATH.write_text(output, encoding="utf-8")
    print(f"written to {OUTPUT_PATH}")
    return output


def main() -> None:
    if not smoke_test():
        print("\nAborting before the full grid run -- fix the smoke test failure first.")
        sys.exit(1)

    print("\nSmoke test passed. Running the full grid (this will take a while)...\n")
    run_full_grid()

    print("\nAnalyzing results...\n")
    analyze()


if __name__ == "__main__":
    main()
