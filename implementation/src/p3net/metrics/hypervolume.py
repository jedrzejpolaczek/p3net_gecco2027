"""
Hypervolume indicator over an arbitrary objective front.

TODO:
- Implement hypervolume computation over a set of objective vectors given a
  reference/nadir point, generic in the number of objectives.
- Support computing hypervolume relative to an externally supplied
  reference front (rather than a fixed reference point), for cases with no
  known oracle front. This module only computes the indicator given such a
  front -- constructing it (e.g. the paper's own candidate definition, the
  union of all points evaluated by any compared method across all runs) is
  an experiments/ concern (experiments/reporting/ or
  experiments/scripts/generate_report.py), not this module's.

Reference: chapters/v003/results/main.tex ("Metrics" -- TODO on the
best-known-front definition, which is an experiments/-level open decision,
not a library one); chapters/v003/notes/main.tex ("Best-known-front
definition for the hypervolume fallback... Open").
"""
