"""
TODO:
- Test delta_hat_F trains on pairwise fitness differences derived from
  H_t.
- Test delta_hat_F(x, x') approximates f1(x) - f1(x') on a synthetic
  dataset with a known ground-truth relationship.
- Test behaviour is undefined/guarded when no linkage tree exists yet
  (relative surrogate cannot pair with NSGA-II -- this should fail
  loudly, not silently).

Reference: src/p3net/surrogates/relative_linkage_aware.py;
chapters/v003/problem_formulation/main.tex ("Surrogate model").
"""
