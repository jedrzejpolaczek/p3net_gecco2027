"""
Generic multi-objective machinery: Pareto dominance/front, fidelity ladder,
evaluation-noise handling.

Library-scope note: f1 and f2 (or however many objectives a concrete
problem has) are always user-supplied callables over a Genotype -- this
module never hardcodes "validation error" or "computational cost proxy".
The concrete objectives for the NAS experiment (f1 via a benchmark query,
f2 as an analytic cost computation) are wired in
experiments/substrates/*.py, which expose them as plain callables this
module's dominance/front machinery can consume.

TODO:
- Implement Pareto dominance over an arbitrary-length objective vector
  (not fixed at two objectives), and a nondominated-front operator, usable
  both for a persistent archive and for one-iteration-local candidate
  selection (the pattern methods/p3net.py needs for its step-4 C*
  selection).
- Implement a generic fidelity-ladder abstraction: an ordered sequence of
  "resource levels" r_1 < ... < r_K, where each level is an opaque
  configuration object (not assumed to be "epoch count" -- a concrete
  problem may pack epochs, resolution, or anything else into it). The
  library must not assume what a level contains, only that levels are
  ordered and that a caller can ask "evaluate objective X at level r_k".
- Implement generic evaluation-noise handling: given a callable that may be
  stochastic, support evaluating it over s repeats/seeds and reducing via
  median (or a user-supplied reducer) for deterministic downstream use.
  Must be a genuine no-op (not dead code, not skipped) when s = 1, since a
  deterministic substrate is a valid, common case, not a special one.
- None of the above may reference NAS-specific concepts (network,
  architecture, training) -- keep this file provably reusable outside the
  paper's domain.

Reference (generic mechanism only): chapters/v003/problem_formulation/
main.tex ("Multi objective formulation", "Multi fidelity evaluation",
"Evaluation noise"). Concrete f1/f2 wiring for this paper's experiment:
experiments/substrates/*.py.
"""
