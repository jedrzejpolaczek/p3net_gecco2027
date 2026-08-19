"""
Single entry point for the P3-eLyMPuS isolation experiment
(notes/plans/experiments-przewozniczek-plan.md, Faza 4): smoke test ->
full grid run -> statistical analysis, mirroring the sibling
experiments-bartnik package's run_bartnik_isolation.py's own pipeline
shape.

Tests `przewozniczek_p3elympus` (P3-eLyMPuS, reconstructed and generalised
from binary to k-ary categorical domains -- `przewozniczek2026lympus`)
against the SAME baseline set `p3net` itself is compared against, plus
`p3net` itself as a direct engine-vs-engine reference point on the
identical search space and budgets. Direct diagnostic test of hypotheses
(i)-(ii) from `conclusions/main.tex` ("Why the results are what they
are"): does the search engine/surrogate class matter, or does
architecture-only NAS-Bench-201 itself (iii) explain why P3Net separates
from nothing on the two joint benchmarks.

Aborts before the (expensive) grid run if the smoke test fails.

Usage (from implementation/experiments-przewozniczek):
    uv run python scripts/run_przewozniczek_isolation.py

Writes results/przewozniczek_isolation_result.md with the Wilcoxon +
Holm-Bonferroni + Cliff's delta result for przewozniczek_p3elympus vs.
each baseline, per budget tested.
"""

from __future__ import annotations

import statistics
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
OUTPUT_PATH = EXPERIMENTS_ROOT / "results" / "przewozniczek_isolation_result.md"

SEARCH_SPACE = "nas_bench_201"
PRIMARY_METHOD = "przewozniczek_p3elympus"
# Exactly the same baseline set p3net's own ablation grid is compared
# against (Table tab:ablation-grid), plus p3net itself as a direct
# engine-vs-engine reference point (plan's Faza 4).
BASELINES = (
    "random_search",
    "sh_emoa",
    "tpe",
    "mo_bohb",
    "nsga_net",
    "nsganetv2",
    "p3_alone",
    "p3_absolute",
    "p3net",
)
METHODS = (PRIMARY_METHOD, *BASELINES)
BUDGETS = (100, 350)


def smoke_test() -> bool:
    """One tiny, real-data run confirming the whole path (config ->
    search space -> substrate -> real nats_bench query -> result) works
    for przewozniczek_p3elympus specifically before committing to the
    full grid. Returns False (never raises) on any failure."""
    print("Running smoke test (budget=12, przewozniczek_p3elympus, nas_bench_201)...")
    try:
        result = run_single(
            load_method_config(PRIMARY_METHOD),
            load_search_space_config(SEARCH_SPACE),
            budget=12,
            seed=1,
        )
    except Exception as exc:  # noqa: BLE001 -- deliberately broad: any failure here means "don't proceed"
        print(f"SMOKE TEST FAILED: {exc!r}")
        return False

    if result.state.evaluations_used != 12:
        print(f"SMOKE TEST FAILED: expected 12 evaluations, got {result.state.evaluations_used}")
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
    """R=30 seeds x 2 budgets x 10 methods = 600 real-data points,
    skipping anything already persisted under results/raw/."""
    points = enumerate_grid(methods=list(METHODS), search_spaces=[SEARCH_SPACE], budgets=list(BUDGETS))
    written, skipped = run_grid(points, skip_cached=True, show_progress=True)
    print(f"ran {len(written)}/{len(points)} grid points ({len(skipped)} already cached)")


def analyze() -> str:
    """Wilcoxon signed-rank + Holm-Bonferroni + Cliff's delta,
    przewozniczek_p3elympus vs. each baseline, per budget -- the same
    stats/significance.py machinery the main comparison grid uses."""
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
        primary_scores = scores_by_seed(PRIMARY_METHOD, budget)
        for baseline in BASELINES:
            baseline_scores = scores_by_seed(baseline, budget)
            shared_seeds = sorted(set(primary_scores) & set(baseline_scores))
            if len(shared_seeds) < 2:
                print(
                    f"budget={budget} baseline={baseline}: skipped, only "
                    f"{len(shared_seeds)} paired seed(s) available"
                )
                continue
            comparisons.append(
                Comparison(
                    baseline=baseline,
                    benchmark=SEARCH_SPACE,
                    budget=budget,
                    p3net_scores=tuple(primary_scores[s] for s in shared_seeds),
                    baseline_scores=tuple(baseline_scores[s] for s in shared_seeds),
                )
            )

    results = compare_p3net_to_baselines(comparisons)

    lines = [
        "# P3-eLyMPuS isolation experiment: przewozniczek_p3elympus vs. the p3net baseline set",
        "",
        "Architecture-only NAS-Bench-201 (no Theta), testing this project's own k-ary generalisation "
        "of P3-eLyMPuS (przewozniczek2026lympus) against exactly the baseline set p3net itself is "
        "compared against, plus p3net as a direct engine-vs-engine reference point "
        "(conclusions/main.tex, \"Why the results are what they are\").",
        "",
        "| Budget | Baseline | n | Median przewozniczek_p3elympus | Median baseline | Adj. p | Cliff's delta | Reject H0 |",
        "|---|---|---|---|---|---|---|---|",
    ]

    for result in results:
        c = result.comparison
        lines.append(
            f"| {c.budget} | {c.baseline} | {len(c.p3net_scores)} | "
            f"{statistics.median(c.p3net_scores):.4f} | {statistics.median(c.baseline_scores):.4f} | "
            f"{result.adjusted_p_value:.4f} | {result.effect_size:+.3f} | {result.reject_null} |"
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
