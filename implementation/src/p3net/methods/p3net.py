"""
P3Net: P3 engine + relative, linkage-aware surrogate delta_hat_F. The
library's primary export.

TODO:
- Implement the full search loop from Proposed Optimizer, Figure
  fig:p3net-loop:
  1. P3 generates candidates via the optimal-mixing sweep
     (search_engines/p3/).
  2. Every proposal is scored relative to its immediate sweep predecessor
     via delta_hat_F.
  3. Tentative acceptance iff delta_hat_F predicts nonnegative improvement
     (zero threshold by default; must be a constructor/config parameter,
     not hardcoded, since callers need to sweep it).
  4. On sweep completion or kappa cutoff, select C* = candidates
     nondominated in (f_hat_1, f2) among this iteration's sweep outcomes
     only (not pooled across iterations -- avoids comparing against a
     drifting surrogate). Use problem/objectives.py's generic
     dominance/front operator.
  5. Fully evaluate every x in C* via the caller-supplied objective
     callable(s) (the library does not know what substrate answers this --
     that is supplied by whoever constructs this method, e.g.
     experiments/substrates/*.py).
  6. Update H_t, retrain delta_hat_F, rebuild the linkage tree.
- Expose chain depth kappa and the step-3 acceptance threshold as
  constructor parameters with sensible defaults (kappa defaulting to
  eLyMPuS's 2*ceil(log2(n)) bound, n = the genotype's dimensionality as
  reported by its SearchSpace; threshold defaulting to 0) -- callers (e.g.
  experiments/ running the paper's kappa/threshold sensitivity sweep) must
  be able to override both without editing this module.
- Reject genotypes failing the caller-supplied Validity check prior to
  surrogate scoring (step order matters).
- Apply the deduplication cache (harness/evaluation_cache.py) -- duplicates
  already in H_t skip reevaluation.
- Operate exclusively at whatever single fidelity level the caller
  configures (P3Net's own paper usage fixes this at r_K and never touches
  the fidelity ladder from problem/objectives.py at all -- but the library
  itself should not assume "no multi-fidelity" as a permanent constraint,
  only as this method's current behaviour).

Reference: chapters/v003/proposed_optimizer/main.tex (entire section, esp.
"Search loop", "Chain depth (kappa)", "Constraint handling",
"Deduplication", "Fidelity scope"). Concrete parameterisation used for the
paper's experiment: experiments/configs/methods/p3net.yaml.
"""
