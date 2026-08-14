"""
P3's population pyramid.

TODO:
- Implement an ordered pyramid of populations of growing size (not a single
  fixed-size population).
- Implement the "parameter-less" growth rule: add a new level only once
  existing levels stop yielding improved solutions.
- Implement promotion of a solution up the pyramid; note this canonically
  requires a real fitness evaluation at every accepted local improvement, not
  only at the end -- this directly determines the budget consumption of the
  surrogate-free "P3 alone" ablation (methods/p3_alone.py) and must be
  accounted for honestly, not hidden behind a cheaper mock.

Reference: chapters/v003/related_work/main.tex ("Structurally, P3 replaces a
single fixed-size population...", Figure fig:p3-pyramid).
"""
