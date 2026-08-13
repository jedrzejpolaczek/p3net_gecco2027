"""
Seed policy: R (independent search runs) vs s (evaluation-noise repeats).

TODO:
- Maintain the fixed, published seed list of R = 10 seeds per method
  (JAHS-Bench-201's recommended minimum), shared identically across all
  methods.
- Keep R strictly distinct from s (repeats of a single query under
  substrate stochasticity, problem/objectives.py) -- both benchmarks used
  here are deterministic, so s = 1 throughout, but the two concepts must
  not collapse into a single "seed" parameter in code.

Reference: chapters/v003/problem_formulation/main.tex ("Evaluation noise"
-- "s should not be confused with R"); chapters/v003/results/main.tex
("Budgets, seeds, stopping").
"""
