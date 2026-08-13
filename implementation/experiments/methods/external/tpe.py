"""
Tree-structured Parzen Estimator (TPE) baseline (sanity check).

TODO:
- Wrap an established TPE implementation (e.g. as used in the
  Optuna/Hyperopt ecosystem) over the same discretised joint genotype
  encoding (experiments/search_spaces/nas_genotype.py) as every other arm.
- Apply the shared dedup cache, budget/seed/stopping-rule handling
  identically to every other arm.

Reference: chapters/v003/results/main.tex ("Baselines").
"""
