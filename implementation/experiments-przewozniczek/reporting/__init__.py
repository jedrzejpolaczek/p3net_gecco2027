"""
experiments.reporting -- turns raw per-run results (results/raw/*.json,
scripts/run_experiment.py's output) into the paper's Results-section
artifacts: the fixed-budget summary table and the convergence/Pareto/
sensitivity/diagnostics figures. scripts/generate_report.py is the entry
point that renders these into results/figures/ and results/tables/, in
the order chapters/v003/results/main.tex promises.

Reference: chapters/v003/results/main.tex ("Findings" TODO block).
"""

from reporting._common import (
    RawRun,
    construct_best_known_front,
    load_raw_run,
    load_raw_runs,
    nadir_reference_point,
)
from reporting.plots import (
    SensitivityPoint,
    convergence_curve_figure,
    duplication_rate_figure,
    pareto_front_progression_figure,
    sensitivity_figure,
    surrogate_calibration_figure,
    surrogate_quality_figure,
)
from reporting.tables import (
    MAIN_COMPARISON_METHODS,
    SummaryRow,
    SweepCompletionRow,
    fixed_budget_summary_table,
    p3_alone_sweep_completion_table,
    render_summary_table_markdown,
    render_sweep_completion_table_markdown,
)

__all__ = [
    "MAIN_COMPARISON_METHODS",
    "RawRun",
    "SensitivityPoint",
    "SummaryRow",
    "SweepCompletionRow",
    "construct_best_known_front",
    "convergence_curve_figure",
    "duplication_rate_figure",
    "fixed_budget_summary_table",
    "load_raw_run",
    "load_raw_runs",
    "nadir_reference_point",
    "p3_alone_sweep_completion_table",
    "pareto_front_progression_figure",
    "render_summary_table_markdown",
    "render_sweep_completion_table_markdown",
    "sensitivity_figure",
    "surrogate_calibration_figure",
    "surrogate_quality_figure",
]
