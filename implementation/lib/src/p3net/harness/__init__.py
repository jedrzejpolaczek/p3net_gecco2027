"""
p3net.harness -- generic evaluation infrastructure: deduplication cache,
seed policy (R vs s), and the pluggable-stopping-rule Runner.

TODO:
- Re-export EvaluationCache, Runner, StoppingRule, and the seed-list
  utilities once implemented.

Reference: chapters/v003/results/main.tex ("Fairness controls" -- the
*mechanism* of a shared, identically-applied cache is generic; using it
identically across nine paper-specific baselines is an experiments/
concern).
"""
