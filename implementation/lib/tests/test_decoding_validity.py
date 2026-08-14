"""
TODO:
- Test the generic Decoder protocol accepts any user-supplied callable
  Genotype -> T, without assuming what T is.
- Test the generic Validity protocol/filter correctly separates valid
  (g(x) <= 0) from invalid genotypes given a synthetic g.
- Test invalid candidates are rejected BEFORE surrogate scoring in
  p3net.methods.p3net's search loop.
- The concrete NAS decoder/validity check (path-existence through a cell
  graph) gets its own test at
  ../experiments/tests/test_nas_search_space.py -- do not duplicate
  NAS-specific assertions here.

Reference: src/p3net/problem/decoding.py;
chapters/v003/proposed_optimizer/main.tex ("Constraint handling", generic
mechanism only).
"""
