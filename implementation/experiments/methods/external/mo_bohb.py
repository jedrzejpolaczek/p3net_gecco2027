"""
MO-BOHB baseline (Multi-Objective Bayesian Optimization Hyperband).

TODO:
- Wrap an established MO-BOHB implementation (as used by
  guerreroviu2021bagofbaselines) rather than reimplementing BOHB from
  scratch.
- Note this baseline is Hyperband-based and thus naturally fidelity-aware
  -- decide explicitly whether/how it is allowed to consume
  p3net.problem's generic fidelity-ladder abstraction while every other arm
  in the main comparison operates only at r_K, and document that decision
  rather than leaving it implicit.
- Adapt its interface to the shared harness (dedup cache, budgets, seeds,
  stopping rule) identically to every other arm.

Reference: chapters/v003/results/main.tex ("Baselines");
chapters/v003/problem_formulation/main.tex ("Multi fidelity evaluation" --
"useful should a future multi-fidelity baseline (e.g. a Hyperband-based
method) be added").
"""
