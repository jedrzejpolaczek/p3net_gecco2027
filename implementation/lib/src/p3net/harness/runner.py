"""
Generic search-loop driver: budget accounting + pluggable stopping rule.

Library-scope note: this module knows about "a method" (anything exposing
the shape methods/p3net.py implements: propose/evaluate/update against a
budget) and "a full-evaluation budget" -- nothing about {50, 100, 200}
evaluations, R = 10 seeds, or the exploration-collapse criterion
bartnik2026evolutionary needed for NAS-Bench-201-scale spaces. Those
concrete numbers and that concrete criterion belong to the paper's
experiment (configs/experiment/budgets.yaml and
experiments/stopping_rules.py), not to the library.

TODO:
- Implement a `Runner` that drives an arbitrary method against an arbitrary
  black-box objective for a fixed full-evaluation budget (an integer count
  of calls to the true objective, never to a surrogate), recording the
  resulting observation dataset (H_t-style: every (genotype, objective
  vector) pair from a full evaluation).
- Define a `StoppingRule` protocol: given the run's state so far, return
  whether to stop. Ship one default implementation (stop once the budget is
  exhausted) as the library's baseline behaviour. Do NOT bake in any
  domain-specific "premature convergence" heuristic here -- that is a
  pluggable StoppingRule a caller supplies (see
  experiments/stopping_rules.py for the paper's own exploration-collapse
  criterion).
- Support running R independent repetitions with a caller-supplied seed
  list and identical initialization scheme; the library owns the mechanics
  of "run N times with these seeds", not the choice of R or which seeds
  (that choice, e.g. R = 10 with a fixed published seed list, is an
  experiments/ concern -- harness/seeds.py in this library only provides
  the R-vs-s distinction as a reusable utility).

Reference (generic mechanism only): chapters/v003/results/main.tex
("Budgets, seeds, stopping" -- the *mechanism* of budget accounting and a
pluggable stopping rule is generic; the *specific* tiers, R, and
convergence criterion described there are experiments/ concerns).
"""
