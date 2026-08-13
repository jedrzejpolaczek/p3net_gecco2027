"""
kappa / acceptance-threshold sensitivity sweep for P3Net specifically.

TODO:
- Sweep kappa over {1, ceil(log2(n)), 2*ceil(log2(n)), infinity} and the
  step-3 acceptance threshold over {0, epsilon, 2*epsilon} for a fixed
  epsilon > 0, jointly, constructing p3net.methods.p3net with each
  combination via its constructor parameters (library's p3net.py exposes
  both as configurable, not hardcoded).
- Report fixed-budget hypervolume (p3net.metrics.hypervolume) and surrogate
  rank correlation (experiments/metrics/surrogate_quality.py) as a function
  of both parameters (feeds experiments/reporting/plots.py).

Reference: chapters/v003/results/main.tex ("Surrogate error accumulation
(kappa and acceptance threshold)").
"""
