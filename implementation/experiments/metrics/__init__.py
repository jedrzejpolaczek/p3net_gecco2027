"""
experiments.metrics -- diagnostics specific to this paper's research
question: surrogate quality tracking and genotype duplication rate. Generic
MOO indicators (hypervolume, IGD+) live in the library (p3net.metrics)
instead.

Reference: chapters/v003/results/main.tex ("Metrics", "Diagnostics").
"""

from metrics.diagnostics import ArchiveTurnoverPoint, archive_turnover, duplication_rate
from metrics.surrogate_quality import (
    SurrogateQualityPoint,
    pairwise_comparison_accuracy,
    rank_correlation,
    surrogate_quality_trace,
)

__all__ = [
    "ArchiveTurnoverPoint",
    "archive_turnover",
    "duplication_rate",
    "SurrogateQualityPoint",
    "pairwise_comparison_accuracy",
    "rank_correlation",
    "surrogate_quality_trace",
]
