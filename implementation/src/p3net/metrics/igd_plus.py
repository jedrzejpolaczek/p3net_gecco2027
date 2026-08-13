"""
Inverted Generational Distance plus (IGD+) against a known oracle front.

TODO:
- Implement IGD+ given a set of evaluated objective vectors and an
  externally supplied, exact oracle Pareto front.
- This module has no opinion on which benchmarks have an enumerable oracle
  front -- that classification (e.g. NAS-HPO-Bench-II yes, JAHS-Bench-201
  no, per the paper's Category 1 / Category 2 split) and the guard against
  calling this on a benchmark without one belong to whoever calls this
  module (experiments/metrics/ or experiments/reporting/), not to this
  generic indicator itself.

Reference: chapters/v003/results/main.tex ("Metrics");
chapters/v003/related_work/main.tex (Category 1 / Category 2 definitions --
context for callers, not this module's concern).
"""
