"""
TODO:
- Test fixed-budget hypervolume computation against a known small example.
- Test hypervolume relative to an externally supplied reference front (the
  best-known-front fallback case), given a fixed synthetic front -- this
  test does not construct that front itself (that is an experiments/
  concern), only verifies the computation given one.
- Test IGD+ against a known small enumerable oracle front.
- Both metrics must work for an arbitrary number of objectives, not just
  two -- assert this explicitly with a 3-objective synthetic case.

Note: surrogate-quality (rank correlation vs |H_t|) and genotype
duplication-rate diagnostics are experiments-specific and tested at
experiments/tests/test_experiment_metrics.py instead.

Reference: src/p3net/metrics/hypervolume.py, igd_plus.py;
chapters/v003/results/main.tex ("Metrics").
"""
