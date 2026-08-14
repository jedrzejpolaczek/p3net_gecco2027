"""
p3net -- a linkage-learning search engine (P3) paired with a relative,
linkage-aware surrogate, for black-box combinatorial (+ optionally
discretised-continuous) optimisation problems.

This is the library. It has no knowledge of neural architecture search,
JAHS-Bench-201, NAS-HPO-Bench-II, or any other baseline method (NSGA-II,
SH-EMOA, MO-BOHB, TPE) -- those live in the sibling experiments/ package,
which reproduces the GECCO 2027 paper (chapters/v003) by consuming this
library the same way any external user would.

TODO:
- Re-export the public entry points once implemented: the generic
  SearchSpace/Genotype/Decoder/Validity types (problem/), the P3 search
  engine (search_engines/p3/), the surrogates (surrogates/), the P3Net
  method itself (methods/p3net.py), the evaluation cache and generic Runner
  (harness/), and the generic multi-objective metrics (metrics/).
- This is the package's public API surface -- keep it deliberately small
  and stable; anything not re-exported here is an implementation detail
  experiments/ (or any other consumer) should not depend on.

Reference: chapters/v003/proposed_optimizer/main.tex (P3Net as a whole);
see README.md for the library/experiments split rationale.
"""
