"""
experiments.methods -- the eight baselines/ablations P3Net is compared
against (everything in Table tab:ablation-grid except P3Net itself, which
is p3net.methods.p3net from the library), each wiring a search engine
(p3net.search_engines.p3 or experiments.search_engines.nsga2) to a
surrogate (p3net.surrogates.* or none) into a runnable arm.

TODO:
- Re-export all method entry points once implemented, matching
  experiments/configs/methods/*.yaml one-to-one (minus p3net.yaml, which
  configures the library's own p3net.methods.p3net directly).

Reference: chapters/v003/results/main.tex ("Baselines", Table
tab:ablation-grid).
"""
