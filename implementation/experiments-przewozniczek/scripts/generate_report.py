"""
Produce the Results-section tables/figures from accumulated raw runs.

Loads every results/raw/*.json (scripts/run_experiment.py's output),
renders reporting/tables.py's fixed-budget summary table and P3-alone
sweep-completion side table to results/tables/*.md, and
reporting/plots.py's convergence, Pareto-progression, and
duplication-rate figures to results/figures/*.png -- one convergence
figure per (search_space, budget) present, one Pareto-progression figure
per (search_space, budget, method) present, and one duplication-rate
figure overall.

Follows the reporting order chapters/v003/results/main.tex promises:
surrogate quality first -- reporting.surrogate_quality_figure, built from
p3net.methods.p3net.P3Net's own live surrogate_quality_log (predicted vs.
true delta at the |H_t| the surrogate actually scored it at, persisted per
run by scripts/run_experiment.py's diagnostics), NOT a post-hoc refit on
results/raw/'s persisted H_t alone -- skipped (with no file written) if no
loaded run carries that diagnostic, e.g. raw runs persisted before this
capability existed; convergence next; Pareto front and hypervolume
comparisons (the fixed-budget summary table, which already carries
hypervolume); then the kappa/acceptance-threshold sensitivity analysis
(skipped -- scripts/run_kappa_sensitivity.py is not implemented yet) and
the duplication-rate diagnostic.

Reference: chapters/v003/results/main.tex ("Findings" TODO block, which
fixes this exact ordering).

The CLI entry point (not the importable generate_report() function itself,
which stays a pure tables/figures writer for callers like
tests/test_reporting.py that don't want an archival side effect) also
archives the just-written tables/figures, plus results/raw/, into a fresh,
auto-named results/archive/<name>/ folder by default
(scripts/archive_snapshot.py) -- so results/tables/ and results/figures/
being overwritten on every run never loses a state nobody meant to throw
away. Pass --no-archive to skip this for quick, throwaway iteration.
"""

from __future__ import annotations

import argparse
from pathlib import Path

from reporting import (
    MAIN_COMPARISON_METHODS,
    convergence_curve_figure,
    duplication_rate_figure,
    fixed_budget_summary_table,
    load_raw_runs,
    p3_alone_sweep_completion_table,
    pareto_front_progression_figure,
    render_summary_table_markdown,
    render_sweep_completion_table_markdown,
    surrogate_calibration_figure,
    surrogate_quality_figure,
)
from scripts.archive_snapshot import archive_snapshot, auto_snapshot_name

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
RESULTS_DIR = EXPERIMENTS_ROOT / "results"
RAW_RESULTS_DIR = RESULTS_DIR / "raw"
TABLES_DIR = RESULTS_DIR / "tables"
FIGURES_DIR = RESULTS_DIR / "figures"


def _write_tables(runs, tables_dir: Path) -> list[Path]:
    tables_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    summary_rows = fixed_budget_summary_table(runs)
    summary_path = tables_dir / "fixed_budget_summary.md"
    summary_path.write_text(render_summary_table_markdown(summary_rows), encoding="utf-8")
    written.append(summary_path)

    sweep_rows = p3_alone_sweep_completion_table(runs)
    if sweep_rows:
        sweep_path = tables_dir / "p3_alone_sweep_completion.md"
        sweep_path.write_text(render_sweep_completion_table_markdown(sweep_rows), encoding="utf-8")
        written.append(sweep_path)

    return written


def _write_figures(runs, figures_dir: Path) -> list[Path]:
    figures_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []

    search_space_budgets = sorted({(r.search_space, r.budget) for r in runs})
    for search_space, budget in search_space_budgets:
        fig = convergence_curve_figure(runs, search_space=search_space, budget=budget)
        path = figures_dir / f"convergence__{search_space}__budget{budget}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        written.append(path)

    two_objective_combos = sorted(
        {
            (r.search_space, r.budget, r.method)
            for r in runs
            if r.objectives and all(len(p) == 2 for p in r.objectives)
        }
    )
    for search_space, budget, method in two_objective_combos:
        fig = pareto_front_progression_figure(
            runs, search_space=search_space, budget=budget, method=method
        )
        path = figures_dir / f"pareto_progression__{method}__{search_space}__budget{budget}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        written.append(path)

    if any(r.diagnostics.get("duplication_rate") is not None for r in runs):
        fig = duplication_rate_figure(runs)
        path = figures_dir / "duplication_rate.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        written.append(path)

    if any(r.diagnostics.get("surrogate_quality_log") for r in runs):
        fig = surrogate_quality_figure(runs, method="p3net")
        path = figures_dir / "surrogate_quality__p3net.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        written.append(path)

        # Same source log, a second, independent read (magnitude
        # calibration, not just sign agreement) -- Phase 1 of this
        # session's pyramid/surrogate investigation plan.
        fig = surrogate_calibration_figure(runs, method="p3net")
        path = figures_dir / "surrogate_calibration__p3net.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        written.append(path)

    return written


def generate_report(
    *,
    raw_results_dir: Path = RAW_RESULTS_DIR,
    tables_dir: Path = TABLES_DIR,
    figures_dir: Path = FIGURES_DIR,
) -> tuple[list[Path], list[Path]]:
    """Returns (table paths written, figure paths written).

    Filters to reporting.MAIN_COMPARISON_METHODS before building anything --
    results/raw/ can (and, per configs/methods/p3net_*.yaml's
    `default_grid: false` design, deliberately does) also hold data for
    methods outside the paper's eleven documented arms, e.g. the
    kappa/threshold/design-choice sensitivity ablations. Without this
    filter, every table/figure below derives its method set dynamically
    from whatever runs are passed in (fixed_budget_summary_table's
    Holm-Bonferroni family size, duplication_rate_figure's bar count,
    convergence_curve_figure's line count all would silently grow) --
    filtering once here, rather than patching each of those generic,
    independently-tested functions, keeps this report correct regardless
    of what else lives in results/raw/."""
    runs = load_raw_runs(raw_results_dir)
    runs = [r for r in runs if r.method in MAIN_COMPARISON_METHODS]
    if not runs:
        return [], []
    tables = _write_tables(runs, tables_dir)
    figures = _write_figures(runs, figures_dir)
    return tables, figures


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--raw-results-dir", type=Path, default=RAW_RESULTS_DIR)
    parser.add_argument("--tables-dir", type=Path, default=TABLES_DIR)
    parser.add_argument("--figures-dir", type=Path, default=FIGURES_DIR)
    parser.add_argument("--archive-dir", type=Path, default=RESULTS_DIR / "archive")
    parser.add_argument(
        "--no-archive",
        action="store_true",
        help="Skip auto-archiving this run to results/archive/ (default: archive every run).",
    )
    args = parser.parse_args(argv)

    tables, figures = generate_report(
        raw_results_dir=args.raw_results_dir,
        tables_dir=args.tables_dir,
        figures_dir=args.figures_dir,
    )
    if not tables and not figures:
        print(f"no runs found under {args.raw_results_dir} -- nothing to report")
        return
    print(f"wrote {len(tables)} table(s) to {args.tables_dir}")
    print(f"wrote {len(figures)} figure(s) to {args.figures_dir}")
    print(
        "kappa/acceptance-threshold sensitivity: skipped -- "
        "scripts/run_kappa_sensitivity.py is not implemented yet"
    )

    if not args.no_archive:
        snapshot_dir = archive_snapshot(
            auto_snapshot_name(),
            raw_dir=args.raw_results_dir,
            tables_dir=args.tables_dir,
            figures_dir=args.figures_dir,
            archive_dir=args.archive_dir,
        )
        print(f"archived snapshot to {snapshot_dir} (skip with --no-archive)")


if __name__ == "__main__":
    main()
