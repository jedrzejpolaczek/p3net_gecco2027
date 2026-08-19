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
from p3net.problem.objectives import Objectives, dominates, pareto_front

from metrics.surrogate_quality import calibration_r2, pairwise_comparison_accuracy
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
    "surrogate_calibration_figure",
    "surrogate_quality_figure",
]


def _hypervolume_trace(objectives: Sequence[Objectives], reference: Objectives) -> list[float]:
    """Best hypervolume-so-far after each of the first k evaluations, for
    k = 1..len(objectives) -- the convergence curve's y-axis for one run.

    Maintains the nondominated front incrementally instead of calling
    pareto_front on the whole growing prefix at every step: since points
    only ever get added (never removed), a point once found dominated
    stays dominated by that same still-present front member forever, so
    it never needs to be reconsidered -- this is exactly equivalent to
    recomputing pareto_front(seen) fresh at each step, just without the
    redundant O(k) rework of the k-1 already-settled points every time
    (O(k^2) total for one run's trace instead of O(k^3))."""
    trace: list[float] = []
    front: list[Objectives] = []
    for point in objectives:
        if not any(dominates(existing, point) for existing in front):
            front = [existing for existing in front if not dominates(point, existing)]
            front.append(point)
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


def surrogate_quality_figure(
    runs: Sequence[RawRun], *, method: str = "p3net", n_bins: int = 10
) -> Figure:
    """Surrogate quality vs. |H_t|, pooled across every search_space, budget,
    and seed present for `method` (default "p3net" -- the only method whose
    diagnostics carry a "surrogate_quality_log", written live during search
    by p3net.methods.p3net.P3Net; see that class's surrogate_quality_log
    field and scripts/run_experiment.py's _diagnostics). Each logged point is
    (|H_t| at the time delta_hat_F scored a proposal, its predicted delta,
    the true delta once that proposal was actually evaluated). Since
    delta_hat_F is a *relative* surrogate (predicts a signed delta, not an
    absolute value), quality here is pairwise_comparison_accuracy (did the
    predicted delta's sign agree with the true delta's sign) -- rank
    correlation does not apply to a surrogate that never predicts an
    absolute value (metrics/surrogate_quality.py's module docstring).
    Points are bucketed into `n_bins` equal-width bins over the observed
    |H_t| range, and accuracy is computed once per bin from every point
    pooled into it (not a rolling window), so each plotted point rests on
    however many (predicted, true) pairs actually fell in that bin -- bins
    with zero points are skipped rather than interpolated."""
    fig = matplotlib.figure.Figure(figsize=(7, 4))
    ax = fig.add_subplot(111)

    points: list[tuple[int, float, float]] = []
    for run in runs:
        if run.method != method:
            continue
        for entry in run.diagnostics.get("surrogate_quality_log", []):
            points.append((entry["history_size"], entry["predicted_delta"], entry["true_delta"]))

    if not points:
        ax.set_title(f"surrogate quality ({method}) -- no diagnostics data")
        return fig

    sizes = [p[0] for p in points]
    lo, hi = min(sizes), max(sizes)
    if lo == hi:
        # every point shares one |H_t| -- a single bin covering just that
        # value, rather than a degenerate zero-width bin edge computation.
        edges = [lo, hi + 1]
    else:
        width = (hi - lo) / n_bins
        edges = [lo + i * width for i in range(n_bins + 1)]

    bin_centers: list[float] = []
    bin_accuracies: list[float] = []
    bin_counts: list[int] = []
    for i in range(len(edges) - 1):
        low, high = edges[i], edges[i + 1]
        in_bin = [
            (pred, true)
            for size, pred, true in points
            if (low <= size < high) or (i == len(edges) - 2 and size == high)
        ]
        if not in_bin:
            continue
        predicted = [p for p, _ in in_bin]
        true = [t for _, t in in_bin]
        bin_centers.append((low + high) / 2)
        bin_accuracies.append(pairwise_comparison_accuracy(predicted, true))
        bin_counts.append(len(in_bin))

    ax.plot(bin_centers, bin_accuracies, marker="o")
    for x, y, n in zip(bin_centers, bin_accuracies, bin_counts):
        ax.annotate(f"n={n}", (x, y), textcoords="offset points", xytext=(0, 6), fontsize="small")
    ax.axhline(0.5, linestyle="--", linewidth=1, color="grey")  # chance level
    ax.set_ylim(-0.05, 1.05)
    ax.set_xlabel("$|\\mathcal{H}_t|$ at prediction time")
    ax.set_ylabel("pairwise comparison accuracy")
    ax.set_title(f"surrogate quality ({method}): predicted-vs-true delta sign agreement")
    return fig


def surrogate_calibration_figure(runs: Sequence[RawRun], *, method: str = "p3net") -> Figure:
    """Magnitude calibration of delta_hat_F, one bar per search_space --
    a second, independent read on surrogate quality alongside
    surrogate_quality_figure above, which only ever scores sign agreement
    and cannot tell whether the *size* of a predicted improvement means
    anything (metrics.surrogate_quality.calibration_r2's own docstring).
    Grouped by search_space rather than binned by |H_t|, unlike
    surrogate_quality_figure -- the question this answers is whether
    calibration degrades with a dataset's measured epistasis the same way
    acceptance-gate precision did (Results, "Diagnostics: surrogate
    representational capacity"), not how it evolves within one run."""
    fig = matplotlib.figure.Figure(figsize=(7, 4))
    ax = fig.add_subplot(111)

    points_by_space: dict[str, list[tuple[float, float]]] = defaultdict(list)
    for run in runs:
        if run.method != method:
            continue
        for entry in run.diagnostics.get("surrogate_quality_log", []):
            points_by_space[run.search_space].append(
                (entry["predicted_delta"], entry["true_delta"])
            )

    if not points_by_space:
        ax.set_title(f"surrogate calibration ({method}) -- no diagnostics data")
        return fig

    spaces = sorted(points_by_space)
    r2_values = [
        calibration_r2(
            [p for p, _ in points_by_space[space]], [t for _, t in points_by_space[space]]
        )
        for space in spaces
    ]

    ax.bar(spaces, r2_values)
    ax.axhline(0.0, linestyle="--", linewidth=1, color="grey")  # "always predict the mean" level
    ax.set_xlabel("search space")
    ax.set_ylabel("$R^2$ (predicted vs.\\ true delta)")
    ax.set_title(f"surrogate calibration ({method}): predicted-vs-true delta magnitude")
    ax.tick_params(axis="x", rotation=20)
    return fig
