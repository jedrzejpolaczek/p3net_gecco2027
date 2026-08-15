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
surrogate quality is NOT produced here (metrics/surrogate_quality.py
operates on a live, in-memory Observation history mid-run, not on
results/raw/'s persisted H_t alone -- computing it after the fact would
need a fitted surrogate re-trained from the persisted history, which this
script does not attempt); convergence next; Pareto front and hypervolume
comparisons (the fixed-budget summary table, which already carries
hypervolume); then the kappa/acceptance-threshold sensitivity analysis
(skipped -- scripts/run_kappa_sensitivity.py is not implemented yet) and
the duplication-rate diagnostic.

Reference: chapters/v003/results/main.tex ("Findings" TODO block, which
fixes this exact ordering).
"""

from __future__ import annotations

import argparse
from pathlib import Path

from reporting import (
    convergence_curve_figure,
    duplication_rate_figure,
    fixed_budget_summary_table,
    load_raw_runs,
    p3_alone_sweep_completion_table,
    pareto_front_progression_figure,
    render_summary_table_markdown,
    render_sweep_completion_table_markdown,
)

EXPERIMENTS_ROOT = Path(__file__).resolve().parent.parent
RAW_RESULTS_DIR = EXPERIMENTS_ROOT / "results" / "raw"
TABLES_DIR = EXPERIMENTS_ROOT / "results" / "tables"
FIGURES_DIR = EXPERIMENTS_ROOT / "results" / "figures"


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

    return written


def generate_report(
    *,
    raw_results_dir: Path = RAW_RESULTS_DIR,
    tables_dir: Path = TABLES_DIR,
    figures_dir: Path = FIGURES_DIR,
) -> tuple[list[Path], list[Path]]:
    """Returns (table paths written, figure paths written)."""
    runs = load_raw_runs(raw_results_dir)
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


if __name__ == "__main__":
    main()
