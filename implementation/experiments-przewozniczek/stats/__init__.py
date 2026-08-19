"""
experiments.stats -- the statistical comparison plan for this paper.

Reference: chapters/v003/results/main.tex ("Statistical plan").
"""

from stats.significance import (
    Comparison,
    ComparisonResult,
    HolmResult,
    cliffs_delta,
    compare_p3net_to_baselines,
    holm_bonferroni_correction,
)

__all__ = [
    "Comparison",
    "ComparisonResult",
    "HolmResult",
    "cliffs_delta",
    "compare_p3net_to_baselines",
    "holm_bonferroni_correction",
]
