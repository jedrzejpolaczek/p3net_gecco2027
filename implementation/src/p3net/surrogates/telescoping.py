"""
Telescoping construction: reconstructing an absolute f1 estimate along a
sweep chain.

TODO:
- Implement f_hat_1(x_m) = f1(x_0) - sum_i delta_hat_{F_i}(x_{i-1}, x_i),
  telescoping back along the chain of tentatively accepted modifications
  x_0, ..., x_m to the nearest ancestor x_0 with a *known*, fully evaluated
  f1.
- Enforce that x_0 (and the parent used to start a sweep) is always drawn
  from H_t -- never from a transient, surrogate-only individual produced
  mid-sweep. This is a hard invariant, not a suggestion: the construction
  must never bottom out on an unknown f1(x_0).
- Reduce correctly to the single-step case f_hat_1(x') = f1(x) -
  delta_hat_F(x, x') when m = 1.
- Respect the chain-depth bound kappa (harness/runner.py or
  methods/p3net.py owns the actual limit-enforcement; this module just
  needs to support being cut off at an arbitrary chain length).

Reference: chapters/v003/proposed_optimizer/main.tex ("Telescoping
construction", "Parent, donor, and ancestor provenance", "Chain depth
(kappa)").
"""
