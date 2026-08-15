# C3 — Metrics, Statistics & Reporting Components

Everything downstream of a completed run: this paper's own diagnostic
metrics (surrogate quality, duplication rate), the statistical comparison
plan, and the reporting layer that turns accumulated `results/raw/*.json`
into the paper's Results-section tables and figures.

```mermaid
C4Component
  title Component diagram for metrics, stats & reporting

  System_Ext(p3net_metrics, "p3net.metrics", "hypervolume, igd_plus")
  System_Ext(p3net_harness, "p3net.harness", "EvaluationCache, Observation")
  System_Ext(matplotlib, "matplotlib", "Optional reporting extra")

  Container_Boundary(metrics, "metrics/") {
    Component(surrogate_quality, "surrogate_quality.py", "rank_correlation, pairwise_comparison_accuracy, surrogate_quality_trace", "Absolute vs. relative surrogate quality, as a function of |H_t|")
    Component(diagnostics, "diagnostics.py", "duplication_rate, archive_turnover", "Thin EvaluationCache re-export + archive entry/exit tracking")
  }

  Container_Boundary(stats, "stats/") {
    Component(significance, "significance.py", "compare_p3net_to_baselines, holm_bonferroni_correction, cliffs_delta", "Paired Wilcoxon + Holm-Bonferroni over exactly the defined comparison set")
  }

  Container_Boundary(reporting, "reporting/") {
    Component(common, "_common.py", "RawRun, load_raw_run(s), construct_best_known_front, nadir_reference_point", "Deserialises results/raw/*.json; pooled best-known-front construction")
    Component(tables, "tables.py", "fixed_budget_summary_table, p3_alone_sweep_completion_table", "Median/IQR + significance per (search_space, budget, method)")
    Component(plots, "plots.py", "convergence_curve_figure, pareto_front_progression_figure, sensitivity_figure, duplication_rate_figure", "Each returns a Figure, file-writing left to the caller")
  }

  Rel(diagnostics, p3net_harness, "EvaluationCache.duplication_rate re-export")
  Rel(common, p3net_harness, "Observation deserialisation")
  Rel(tables, common, "RawRun, construct_best_known_front, nadir_reference_point")
  Rel(tables, p3net_metrics, "hypervolume_relative_to_best_known_front, igd_plus")
  Rel(tables, significance, "compare_p3net_to_baselines")
  Rel(plots, common, "RawRun, construct_best_known_front, nadir_reference_point")
  Rel(plots, p3net_metrics, "hypervolume")
  Rel(plots, matplotlib, "Figure construction")
```

## Components

| Component | Responsibility | Source |
|---|---|---|
| **surrogate_quality.py** | `rank_correlation` (absolute-style surrogates), `pairwise_comparison_accuracy` (relational surrogates like δ̂_F, which have no absolute prediction to rank-correlate), `surrogate_quality_trace` (refits on growing `H_t` prefixes) | `metrics/surrogate_quality.py` |
| **diagnostics.py** | `duplication_rate` (thin `EvaluationCache` re-export — single source of truth, not a second counting mechanism), `archive_turnover` (entries/exits between consecutive population snapshots) | `metrics/diagnostics.py` |
| **significance.py** | `compare_p3net_to_baselines`: paired Wilcoxon signed-rank + Holm-Bonferroni correction, applied once over exactly the defined comparison set (P3Net vs. every other arm, per benchmark and budget tier) — never every pairwise combination | `stats/significance.py` |
| **_common.py** | `RawRun`/`load_raw_run(s)`: deserialises persisted JSON back into `Observation`-based records, additive `diagnostics` field defaults to `{}` for older files. `construct_best_known_front`/`nadir_reference_point`: the pooled-front construction `p3net.metrics` deliberately leaves to callers | `reporting/_common.py` |
| **tables.py** | `fixed_budget_summary_table`: median/IQR + Holm-corrected significance vs. P3Net, per (search_space, budget, method). `p3_alone_sweep_completion_table`: the paper's own sweep-completion side table | `reporting/tables.py` |
| **plots.py** | `convergence_curve_figure`, `pareto_front_progression_figure`, `sensitivity_figure`, `duplication_rate_figure` — each returns a `matplotlib.figure.Figure`; `matplotlib` is an optional extra | `reporting/plots.py` |

See [C4: Reporting pipeline](../c4/reporting-pipeline.md) for the
best-known-front and summary-table construction in code-level detail.

## Why `reporting/` depends on `_common.py` rather than `metrics/`/`stats/` directly duplicating it

`RawRun`/`construct_best_known_front`/`nadir_reference_point` are needed
by both `tables.py` and `plots.py` — `_common.py` is the single
implementation both import, rather than each reimplementing (and
potentially drifting on) the same best-known-front pooling logic. Neither
`metrics/` nor `stats/` needs this machinery at all: they operate on a
single run's `Observation` history or a paired-scores list respectively,
never on the cross-run pooling `reporting/` alone requires.
