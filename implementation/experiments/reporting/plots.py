"""
Convergence curves, Pareto front progression, sensitivity, and diagnostics
plots. Every function here returns a `matplotlib.figure.Figure` rather
than writing a file directly -- saving to results/figures/ is
scripts/generate_report.py's job, keeping these functions cheaply testable
(assert on the returned Figure's axes/lines) without touching disk.

Reference: chapters/v003/results/main.tex ("Findings" TODO block,
"Diagnostics", "Surrogate error accumulation (kappa and acceptance
threshold)").
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Sequence
from dataclasses import dataclass

import matplotlib.figure
from matplotlib.figure import Figure
from p3net.metrics import hypervolume
from p3net.problem.objectives import Objectives, pareto_front

from reporting._common import RawRun, construct_best_known_front, nadir_reference_point

# Re-exported here since best-known-front construction is credited to
# this module specifically, even though tables.py also needs the same
# implementation (reporting._common is the single source).
__all__ = [
    "construct_best_known_front",
    "convergence_curve_figure",
    "pareto_front_progression_figure",
    "SensitivityPoint",
    "sensitivity_figure",
    "duplication_rate_figure",
]


def _hypervolume_trace(objectives: Sequence[Objectives], reference: Objectives) -> list[float]:
    """Best hypervolume-so-far after each of the first k evaluations, for
    k = 1..len(objectives) -- the convergence curve's y-axis for one run."""
    trace: list[float] = []
    seen: list[Objectives] = []
    for point in objectives:
        seen.append(point)
        front = pareto_front(seen, lambda p: p)
        trace.append(hypervolume(front, reference))
    return trace


def convergence_curve_figure(runs: Sequence[RawRun], *, search_space: str, budget: int) -> Figure:
    """One figure per (search_space, budget): median hypervolume-so-far
    across seeds, one line per method, with an IQR shaded band. The
    reference point is derived from every point in every given run for
    this search_space/budget (weakly worse than everything plotted)."""
    relevant = [r for r in runs if r.search_space == search_space and r.budget == budget]
    fig = matplotlib.figure.Figure(figsize=(8, 5))
    ax = fig.add_subplot(111)
    if not relevant:
        ax.set_title(f"convergence: {search_space} (budget={budget}) -- no runs")
        return fig

    all_points = [p for r in relevant for p in r.objectives]
    reference = nadir_reference_point(all_points)

    by_method: dict[str, list[RawRun]] = defaultdict(list)
    for run in relevant:
        by_method[run.method].append(run)

    for method, method_runs in sorted(by_method.items()):
        traces = [_hypervolume_trace(r.objectives, reference) for r in method_runs if r.objectives]
        if not traces:
            continue
        min_len = min(len(t) for t in traces)
        traces = [t[:min_len] for t in traces]
        steps = list(range(1, min_len + 1))
        medians = [statistics.median(t[i] for t in traces) for i in range(min_len)]
        if len(traces) > 1:
            lo = [min(t[i] for t in traces) for i in range(min_len)]
            hi = [max(t[i] for t in traces) for i in range(min_len)]
            ax.fill_between(steps, lo, hi, alpha=0.15)
        ax.plot(steps, medians, label=method)

    ax.set_xlabel("full evaluations")
    ax.set_ylabel("hypervolume (best-so-far, median across seeds)")
    ax.set_title(f"convergence: {search_space} (budget={budget})")
    ax.legend(fontsize="small")
    return fig


def pareto_front_progression_figure(
    runs: Sequence[RawRun], *, search_space: str, budget: int, method: str
) -> Figure:
    """Scatter of the Pareto front at 25/50/75/100% of the budget, pooled
    across every seed for one (search_space, budget, method) -- only
    meaningful for 2 objectives (f1, f2), matching this paper's setting."""
    relevant = [
        r
        for r in runs
        if r.search_space == search_space and r.budget == budget and r.method == method
    ]
    fig = matplotlib.figure.Figure(figsize=(6, 5))
    ax = fig.add_subplot(111)
    if not relevant:
        ax.set_title(f"Pareto progression: {method}/{search_space} (budget={budget}) -- no runs")
        return fig
    if any(len(p) != 2 for r in relevant for p in r.objectives):
        raise ValueError("pareto_front_progression_figure only supports 2-objective runs")

    checkpoints = (0.25, 0.5, 0.75, 1.0)
    for fraction in checkpoints:
        pooled: list[Objectives] = []
        for run in relevant:
            k = max(1, round(len(run.objectives) * fraction))
            pooled.extend(run.objectives[:k])
        front = pareto_front(pooled, lambda p: p)
        if not front:
            continue
        xs = [p[0] for p in front]
        ys = [p[1] for p in front]
        ax.scatter(xs, ys, label=f"{int(fraction * 100)}% of budget")

    ax.set_xlabel("f1")
    ax.set_ylabel("f2")
    ax.set_title(f"Pareto front progression: {method} / {search_space} (budget={budget})")
    ax.legend(fontsize="small")
    return fig


@dataclass(frozen=True)
class SensitivityPoint:
    """One cell of the kappa / acceptance-threshold joint sweep
    (configs/experiment/kappa_threshold_sweep.yaml). Produced by
    scripts/run_kappa_sensitivity.py (not yet implemented) or supplied
    directly by a caller/test; this module only knows how to plot the
    grid, not how to run it."""

    kappa: int | None
    acceptance_threshold: float
    hypervolume: float
    rank_correlation: float


def sensitivity_figure(
    points: Sequence[SensitivityPoint], *, metric: str = "hypervolume"
) -> Figure:
    """Heatmap of `metric` ("hypervolume" or "rank_correlation") over the
    kappa x acceptance_threshold grid."""
    if metric not in ("hypervolume", "rank_correlation"):
        raise ValueError(f"unknown metric {metric!r}, expected 'hypervolume' or 'rank_correlation'")
    fig = matplotlib.figure.Figure(figsize=(6, 5))
    ax = fig.add_subplot(111)
    if not points:
        ax.set_title(f"sensitivity ({metric}) -- no data")
        return fig

    kappas = sorted({p.kappa for p in points}, key=lambda k: (k is None, k))
    thresholds = sorted({p.acceptance_threshold for p in points})
    grid = [[float("nan")] * len(thresholds) for _ in kappas]
    by_cell = {(p.kappa, p.acceptance_threshold): getattr(p, metric) for p in points}
    for i, kappa in enumerate(kappas):
        for j, threshold in enumerate(thresholds):
            value = by_cell.get((kappa, threshold))
            if value is not None:
                grid[i][j] = value

    image = ax.imshow(grid, aspect="auto", cmap="viridis")
    ax.set_xticks(range(len(thresholds)))
    ax.set_xticklabels([str(t) for t in thresholds])
    ax.set_yticks(range(len(kappas)))
    ax.set_yticklabels(["inf" if k is None else str(k) for k in kappas])
    ax.set_xlabel("acceptance threshold")
    ax.set_ylabel("kappa")
    ax.set_title(f"sensitivity: {metric}")
    fig.colorbar(image, ax=ax)
    return fig


def duplication_rate_figure(runs: Sequence[RawRun]) -> Figure:
    """Bar chart of proposal-time genotype duplication rate
    (metrics/diagnostics.py's `duplication_rate`, persisted per run by
    scripts/run_experiment.py) per method, averaged across every
    search_space/budget/seed present in `runs`. Archive turnover
    (metrics/diagnostics.py's `archive_turnover`) is NOT plotted here: it
    needs per-generation population snapshots that
    scripts/run_experiment.py does not currently persist (only the final
    H_t is written to results/raw/) -- a real gap, documented rather than
    faked with a single final-state snapshot."""
    fig = matplotlib.figure.Figure(figsize=(7, 4))
    ax = fig.add_subplot(111)
    by_method: dict[str, list[float]] = defaultdict(list)
    for run in runs:
        rate = run.diagnostics.get("duplication_rate")
        if rate is not None:
            by_method[run.method].append(rate)
    if not by_method:
        ax.set_title("duplication rate -- no diagnostics data")
        return fig

    methods = sorted(by_method)
    means = [statistics.mean(by_method[m]) for m in methods]
    ax.bar(methods, means)
    ax.set_ylabel("mean proposal-time duplication rate")
    ax.set_title("genotype duplication rate by method")
    ax.tick_params(axis="x", rotation=45)
    return fig
