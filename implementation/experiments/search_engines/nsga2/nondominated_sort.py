"""
NSGA-II nondominated sorting.

TODO:
- Implement standard fast nondominated sorting over the (f1, f2) objective
  space, producing ranked fronts. May reuse p3net.problem's generic Pareto
  dominance primitive as a building block, but the ranking/front-assignment
  algorithm itself is NSGA-II-specific and does not belong in the library.
- This is the selection mechanic NSGA-Net/NSGANetV2 contribute to their
  respective baseline arms (experiments/methods/nsga_net.py,
  nsganetv2.py) -- keep it a faithful, unmodified NSGA-II implementation so
  any gain over it is attributable to P3's dependency-aware variation
  operator, not to a weakened baseline.

Reference: chapters/v003/results/main.tex ("The protocol must not allow
P3Net to be read as 'P3 plus Pareto filtering.'..."); chapters/v003/
related_work/main.tex.
"""
