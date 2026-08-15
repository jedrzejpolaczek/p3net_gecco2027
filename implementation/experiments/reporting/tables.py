"""
Fixed-budget summary table (median, IQR, corrected p-values, effect sizes),
plus the P3-alone "number of full sweeps completed within budget" side
table (chapters/v003/results/main.tex, "Baselines" paragraph).

Per (search_space, budget, method): median/IQR of the metric that
benchmark supports -- IGD+ against a caller-supplied oracle front for a
Category 1 benchmark (an exact oracle front is only enumerable for
NAS-HPO-Bench-II, and only by querying its live tabulated data, which this
module has no opinion on how to obtain -- callers pass `oracle_fronts`
when they have one), or hypervolume relative to the pooled best-known
front (reporting._common.construct_best_known_front) otherwise. Corrected
significance (stats/significance.py) is computed once, over exactly the
defined comparison set -- P3Net vs. every other arm actually present, per
benchmark and budget tier -- never every pairwise combination, since the
Holm-Bonferroni correction count depends on that scope being right.

Reference: chapters/v003/results/main.tex ("This section reports... a
fixed-budget summary table (median, IQR, corrected p values, effect
sizes)... Findings"; "Baselines" paragraph, P3-alone sweep count).
"""

from __future__ import annotations

import statistics
from collections import defaultdict
from collections.abc import Mapping, Sequence
from dataclasses import dataclass

from p3net.metrics import hypervolume_relative_to_best_known_front, igd_plus
from p3net.problem.objectives import Objectives, pareto_front

from reporting._common import RawRun, construct_best_known_front, nadir_reference_point
from stats.significance import Comparison, compare_p3net_to_baselines

P3NET_METHOD_NAME = "p3net"


@dataclass(frozen=True)
class SummaryRow:
    method: str
    search_space: str
    budget: int
    metric: str
    median: float
    iqr: float
    n_runs: int
    adjusted_p_value: float | None = None
    effect_size: float | None = None
    reject_null: bool | None = None


@dataclass(frozen=True)
class SweepCompletionRow:
    search_space: str
    budget: int
    median_sweeps_completed: float
    iqr: float
    n_runs: int


def _iqr(values: Sequence[float]) -> float:
    if len(values) < 2:
        return 0.0
    q1, _, q3 = statistics.quantiles(values, n=4, method="inclusive")
    return q3 - q1


def _run_metric(
    run: RawRun,
    *,
    oracle_front: Sequence[Objectives] | None,
    best_known_front: Sequence[Objectives] | None,
    reference: Objectives | None,
) -> float:
    front = pareto_front(list(run.objectives), lambda p: p)
    if oracle_front is not None:
        return igd_plus(front, oracle_front)
    assert best_known_front is not None and reference is not None
    return hypervolume_relative_to_best_known_front(front, best_known_front, reference)


def fixed_budget_summary_table(
    runs: Sequence[RawRun],
    *,
    oracle_fronts: Mapping[str, Sequence[Objectives]] | None = None,
    alpha: float = 0.05,
) -> list[SummaryRow]:
    oracle_fronts = oracle_fronts or {}
    runs_with_history = [r for r in runs if r.objectives]

    by_space_budget: dict[tuple[str, int], list[RawRun]] = defaultdict(list)
    for run in runs_with_history:
        by_space_budget[(run.search_space, run.budget)].append(run)

    rows: list[SummaryRow] = []
    scores_by_group: dict[tuple[str, int, str], dict[int, float]] = {}

    for (search_space, budget), group_runs in by_space_budget.items():
        oracle_front = oracle_fronts.get(search_space)
        space_runs = [r for r in runs_with_history if r.search_space == search_space]

        best_known_front: list[Objectives] | None = None
        reference: Objectives | None = None
        if oracle_front is None:
            # Reference must be weakly worse than every point that will be
            # scored against it -- derived from every raw point pooled for
            # this search_space (not just the pooled front's own nadir,
            # which can be strictly better than a dominated point that
            # still needs scoring within its own run's front).
            all_space_points = [p for r in space_runs for p in r.objectives]
            reference = nadir_reference_point(all_space_points)
            best_known_front = construct_best_known_front(space_runs)

        by_method: dict[str, list[RawRun]] = defaultdict(list)
        for run in group_runs:
            by_method[run.method].append(run)

        for method, method_runs in by_method.items():
            per_seed_scores = {
                run.seed: _run_metric(
                    run,
                    oracle_front=oracle_front,
                    best_known_front=best_known_front,
                    reference=reference,
                )
                for run in method_runs
            }
            values = list(per_seed_scores.values())
            metric_name = "igd_plus" if oracle_front is not None else "hypervolume_relative"
            rows.append(
                SummaryRow(
                    method=method,
                    search_space=search_space,
                    budget=budget,
                    metric=metric_name,
                    median=statistics.median(values),
                    iqr=_iqr(values),
                    n_runs=len(values),
                )
            )
            scores_by_group[(search_space, budget, method)] = per_seed_scores

    comparisons: list[Comparison] = []
    for (search_space, budget), group_runs in by_space_budget.items():
        p3net_scores = scores_by_group.get((search_space, budget, P3NET_METHOD_NAME))
        if not p3net_scores:
            continue
        other_methods = {r.method for r in group_runs} - {P3NET_METHOD_NAME}
        for method in sorted(other_methods):
            baseline_scores = scores_by_group.get((search_space, budget, method))
            if not baseline_scores:
                continue
            shared_seeds = sorted(set(p3net_scores) & set(baseline_scores))
            if len(shared_seeds) < 2:
                continue  # not enough paired seeds for a Wilcoxon signed-rank test
            comparisons.append(
                Comparison(
                    baseline=method,
                    benchmark=search_space,
                    budget=budget,
                    p3net_scores=tuple(p3net_scores[s] for s in shared_seeds),
                    baseline_scores=tuple(baseline_scores[s] for s in shared_seeds),
                )
            )

    results_by_key = {
        (r.comparison.baseline, r.comparison.benchmark, r.comparison.budget): r
        for r in compare_p3net_to_baselines(comparisons, alpha=alpha)
    }

    updated_rows: list[SummaryRow] = []
    for row in rows:
        result = results_by_key.get((row.method, row.search_space, row.budget))
        updated_rows.append(
            SummaryRow(
                method=row.method,
                search_space=row.search_space,
                budget=row.budget,
                metric=row.metric,
                median=row.median,
                iqr=row.iqr,
                n_runs=row.n_runs,
                adjusted_p_value=result.adjusted_p_value if result else None,
                effect_size=result.effect_size if result else None,
                reject_null=result.reject_null if result else None,
            )
        )
    return updated_rows


def p3_alone_sweep_completion_table(
    runs: Sequence[RawRun], *, method: str = "p3_alone"
) -> list[SweepCompletionRow]:
    """P3-alone's own diagnostic (chapters/v003/results/main.tex,
    "Baselines"): under a tight budget, P3 alone without a surrogate is
    expected to exhaust most or all of the budget within a handful of
    sweeps -- this reads the collapse as budget starvation rather than
    engine failure. `sweeps_completed` is persisted per run by
    scripts/run_experiment.py's diagnostics (methods/p3_alone.py's own
    field); runs persisted before that field existed are silently
    excluded (older raw JSON has no "diagnostics" key)."""
    by_group: dict[tuple[str, int], list[int]] = defaultdict(list)
    for run in runs:
        if run.method != method:
            continue
        sweeps = run.diagnostics.get("sweeps_completed")
        if sweeps is None:
            continue
        by_group[(run.search_space, run.budget)].append(sweeps)

    return [
        SweepCompletionRow(
            search_space=search_space,
            budget=budget,
            median_sweeps_completed=statistics.median(values),
            iqr=_iqr(values),
            n_runs=len(values),
        )
        for (search_space, budget), values in sorted(by_group.items())
    ]


def render_summary_table_markdown(rows: Sequence[SummaryRow]) -> str:
    lines = [
        "| Method | Search space | Budget | Metric | Median | IQR | n | "
        "Adj. p | Effect size | Reject H0 |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for row in sorted(rows, key=lambda r: (r.search_space, r.budget, r.method)):
        p = f"{row.adjusted_p_value:.4f}" if row.adjusted_p_value is not None else "--"
        effect = f"{row.effect_size:.3f}" if row.effect_size is not None else "--"
        reject = "--" if row.reject_null is None else ("yes" if row.reject_null else "no")
        lines.append(
            f"| {row.method} | {row.search_space} | {row.budget} | {row.metric} | "
            f"{row.median:.4f} | {row.iqr:.4f} | {row.n_runs} | {p} | {effect} | {reject} |"
        )
    return "\n".join(lines) + "\n"


def render_sweep_completion_table_markdown(rows: Sequence[SweepCompletionRow]) -> str:
    lines = [
        "| Search space | Budget | Median sweeps completed | IQR | n |",
        "|---|---|---|---|---|",
    ]
    for row in sorted(rows, key=lambda r: (r.search_space, r.budget)):
        lines.append(
            f"| {row.search_space} | {row.budget} | {row.median_sweeps_completed:.1f} | "
            f"{row.iqr:.1f} | {row.n_runs} |"
        )
    return "\n".join(lines) + "\n"
