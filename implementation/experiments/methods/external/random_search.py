"""
Random search baseline (sanity check).

TODO:
- Implement uniform random sampling over the valid-genotype filter from
  p3net.problem.decoding, applied to
  experiments/search_spaces/nas_genotype.py's shared discretised Theta
  encoding.
- Apply the shared dedup cache, budget/seed/stopping-rule handling
  identically to every other arm.

Reference: chapters/v003/results/main.tex ("Baselines" -- "random search
and the Tree-structured Parzen Estimator (TPE) as sanity baselines").
"""
