"""
TODO:
- Test cache keys include genotype, experiment type, and protocol version
  string.
- Test a protocol-version change invalidates stale entries automatically.
- Test duplicate genotypes skip reevaluation identically across every
  methods/* arm (not just P3Net).
- Test duplication-rate counting happens at proposal time, independent of
  cache hit/miss.

Reference: src/p3net/harness/evaluation_cache.py;
chapters/v003/results/main.tex ("Fairness controls", "Reproducibility",
"Diagnostics").
"""
