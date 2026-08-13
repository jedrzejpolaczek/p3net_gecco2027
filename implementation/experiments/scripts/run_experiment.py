"""
Entry point: run a single (method x benchmark x budget x seed) search.

TODO:
- Parse a method config (experiments/configs/methods/*.yaml -- for
  "p3net.yaml" this configures p3net.methods.p3net directly; for every other
  file it configures the corresponding experiments/methods/*.py arm), a
  search-space config (experiments/configs/search_spaces/*.yaml), and a
  budget tier (experiments/configs/experiment/budgets.yaml).
- Instantiate the corresponding method (library's p3net.methods.p3net, or
  an experiments/methods/* arm) against the corresponding
  experiments/substrates/* adapter via p3net.harness.runner (the library's
  generic Runner), configured with experiments/stopping_rules.py's concrete
  StoppingRule, for one seed.
- Persist the resulting H_t (raw per-run observation log) under
  experiments/results/raw/, keyed consistently with
  p3net.harness.evaluation_cache's protocol-version scheme.

Reference: chapters/v003/results/main.tex ("Experimental Setup" as a
whole).
"""
