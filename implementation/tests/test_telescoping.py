"""
TODO:
- Test the single-step case reduces exactly to f_hat_1(x') = f1(x) -
  delta_hat_F(x, x').
- Test the multi-step chain sums delta_hat_{F_i} correctly back to a known
  f1(x_0).
- Test the invariant that x_0 is always drawn from H_t -- construct a case
  where it would otherwise bottom out on a surrogate-only individual and
  assert this is rejected.

Reference: src/p3net/surrogates/telescoping.py;
chapters/v003/proposed_optimizer/main.tex ("Telescoping construction",
"Parent, donor, and ancestor provenance").
"""
