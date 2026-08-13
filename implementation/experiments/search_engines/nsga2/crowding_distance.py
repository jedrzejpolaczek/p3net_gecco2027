"""
NSGA-II crowding-distance selection.

TODO:
- Implement standard crowding-distance computation within a front, used to
  select within a rank when trimming to population size.
- Keep this faithful to standard NSGA-II -- it is the exact mechanic P3Net's
  optimal mixing sweep (p3net.methods.p3net, via p3net.search_engines.p3) is
  being compared against (Introduction's central question).

Reference: chapters/v003/introduction/main.tex ("Central question and
contribution"); chapters/v003/related_work/main.tex.
"""
