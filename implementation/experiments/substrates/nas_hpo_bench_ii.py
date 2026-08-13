"""
NAS-HPO-Bench-II adapter (Category 1: fixed grid lookup table, exact oracle
front).

TODO:
- Wrap the NAS-HPO-Bench-II lookup table as the query substrate, restricted
  to its exhaustively tabulated range (up to 12 training epochs, three
  recorded seeds/entry).
- Do NOT query the benchmark's separate 200-epoch GIN+MLP surrogate
  extrapolation -- r_K for this benchmark is fixed at the tabulated range
  only; wire this as a hard constraint (e.g. an assertion / config bound),
  not a comment-only convention.
- Encode its search space: architecture (fixed cell topology) + learning
  rate + batch size as hyperparameters, via
  experiments/search_spaces/nas_genotype.py.
- Because an exact oracle front is enumerable here, expose whatever is
  needed for p3net.metrics.igd_plus (called from experiments/metrics/ or
  experiments/reporting/) to compute IGD+ against it.

Reference: chapters/v003/related_work/main.tex ("Classifying NAS-HPO-Bench-II
as Category 1..."); chapters/v003/results/main.tex ("Benchmark and search
space").
"""
