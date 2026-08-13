"""
p3net.metrics -- generic multi-objective quality metrics: hypervolume, IGD+.

Only domain-agnostic MOO metrics live here. Surrogate-quality tracking
(rank correlation vs |H_t|) and genotype duplication-rate/archive-turnover
diagnostics are specific to evaluating *this paper's* research question and
live in experiments/metrics/ instead.

TODO:
- Re-export hypervolume and igd_plus entry points once implemented.

Reference: chapters/v003/results/main.tex ("Metrics").
"""
