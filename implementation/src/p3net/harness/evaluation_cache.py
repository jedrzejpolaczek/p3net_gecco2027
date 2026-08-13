"""
Shared deduplication / reproducibility cache.

TODO:
- Implement a cache keyed by (genotype, experiment type, protocol version
  string) covering every setting that affects the recorded value, so any
  settings change invalidates stale entries automatically (pattern from
  bartnik2026evolutionary).
- Skip reevaluation for duplicates already present in H_t; apply this
  identically across every method in methods/, as part of the shared
  harness -- not just inside P3Net's own loop.
- Count genotype duplication rate AT PROPOSAL TIME (every candidate a
  search operator generates, whether or not the cache later intercepts
  it), not at evaluation time -- this is a required diagnostic
  (metrics/diagnostics.py), so the cache needs to expose a proposal-time
  hook distinct from its evaluation-time hit/miss logic.
- This cache must not itself compute f2 (the analytic cost proxy) -- f2 is
  computed directly, without surrogate or cache involvement.

Reference: chapters/v003/proposed_optimizer/main.tex ("Deduplication");
chapters/v003/results/main.tex ("Fairness controls", "Reproducibility",
"Diagnostics").
"""
