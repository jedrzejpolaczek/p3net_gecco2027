"""
Surrogate quality: rank correlation vs |H_t|.

TODO:
- Implement rank correlation (e.g. Spearman/Kendall) between predicted and
  true values, tracked as a function of |H_t| (observation dataset size)
  over the course of search.
- Support both a regression-style surrogate (p3net.surrogates.
  relative_linkage_aware, p3net.surrogates.absolute_regressor) and, if ever
  needed, a relational/pairwise-comparison surrogate via pairwise
  comparison accuracy instead of rank correlation.
- Feed this into the kappa / acceptance-threshold sensitivity analysis
  (experiments/configs/experiment/kappa_threshold_sweep.yaml), which
  reports surrogate rank correlation jointly with fixed-budget hypervolume
  (p3net.metrics.hypervolume).

Reference: chapters/v003/results/main.tex ("Metrics", "Surrogate error
accumulation (kappa and acceptance threshold)").
"""
