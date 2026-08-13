"""
SH-EMOA baseline (multi-objective EA built on SMS-EMOA).

TODO:
- Wrap an established SH-EMOA implementation (the one used by
  guerreroviu2021bagofbaselines for this exact joint setting on these same
  two benchmarks) rather than reimplementing SMS-EMOA from scratch.
- Adapt its interface to the shared harness (p3net.harness.runner): same
  genotype encoding (experiments/search_spaces/nas_genotype.py), dedup
  cache, budget/seed/stopping-rule handling as every other arm.

Reference: chapters/v003/results/main.tex ("Baselines");
chapters/v003/related_work/main.tex ("A systematic comparison of solvers on
this setting...").
"""
