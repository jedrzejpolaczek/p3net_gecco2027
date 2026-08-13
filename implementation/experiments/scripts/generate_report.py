"""
Produce the Results-section tables/figures from accumulated raw runs.

TODO:
- Load all experiments/results/raw/ runs, compute p3net.metrics
  (hypervolume, IGD+ where applicable) and experiments/metrics
  (surrogate_quality, diagnostics), run experiments/stats/significance.py,
  and render experiments/reporting/tables.py + experiments/reporting/
  plots.py outputs into experiments/results/figures/.
- Follow the reporting order promised in the paper: surrogate quality;
  convergence under each fixed evaluation budget; Pareto front and
  hypervolume comparisons across all nine baselines/ablations on both
  benchmarks; the fixed-budget summary table; then the
  kappa/acceptance-threshold sensitivity analysis and the duplication-rate
  diagnostic.

Reference: chapters/v003/results/main.tex ("Findings" TODO block, which
fixes this exact ordering).
"""
