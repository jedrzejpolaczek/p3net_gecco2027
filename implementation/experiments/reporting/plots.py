"""
Convergence curves, Pareto front progression, surrogate-quality curves.

TODO:
- Convergence curves per method/benchmark/budget tier.
- Pareto front progression plots.
- Stability-across-seeds visualisation.
- Surrogate rank correlation vs |H_t| curves
  (experiments/metrics/surrogate_quality.py output).
- kappa / acceptance-threshold sensitivity plots (hypervolume and rank
  correlation as a function of both, per
  experiments/configs/experiment/kappa_threshold_sweep.yaml).
- Genotype duplication-rate diagnostic plots
  (experiments/metrics/diagnostics.py output).
- Construct the "best-known front" (union of all points evaluated by any
  compared method across all runs) that
  p3net.metrics.hypervolume's fallback needs for JAHS-Bench-201 -- this
  aggregation across all methods/runs is this module's responsibility, not
  the library's.

Reference: chapters/v003/results/main.tex ("Findings" TODO block,
"Diagnostics", "Surrogate error accumulation (kappa and acceptance
threshold)").
"""
