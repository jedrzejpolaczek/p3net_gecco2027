"""
Genotype duplication rate and archive turnover diagnostics.

This diagnostic is the empirical test of whether P3's dependency-aware
operator actually generates fewer duplicates than NSGA-II's blind
crossover -- the paper is explicit that duplicates (decoding redundancy)
and variable dependencies (fitness relevance) are different phenomena
that need not coincide; this module measures whether they do, it does not
assume it.

Reference: chapters/v003/introduction/main.tex (NSGA-Net duplication-rate
paragraphs); chapters/v003/results/main.tex ("Diagnostics").
"""

from __future__ import annotations

from dataclasses import dataclass

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.problem.genotype import Genotype


def duplication_rate(cache: EvaluationCache) -> float:
    """Genotype duplication rate, counted at PROPOSAL time -- every
    candidate a search operator generated, whether or not it turned out to
    already be in H_t, measured under the identical joint genotype
    encoding every compared method shares (search_spaces/nas_genotype.py).
    Every methods.*.py arm already routes every proposal through
    EvaluationCache.record_proposal (Stage B integration tests), so this
    is a thin, single-source-of-truth re-export rather than a second
    counting mechanism that could drift from the cache's own bookkeeping.
    """
    return cache.duplication_rate


@dataclass(frozen=True)
class ArchiveTurnoverPoint:
    step: int
    entered: frozenset[Genotype]
    left: frozenset[Genotype]


def archive_turnover(archive_snapshots: list[list[Genotype]]) -> list[ArchiveTurnoverPoint]:
    """Archive turnover over the course of search: for each consecutive
    pair of population/archive snapshots, which genotypes entered and
    which left. `archive_snapshots[i]` is the archive's contents after
    step i (granularity -- one snapshot per full evaluation, per
    generation, ... -- is the caller's choice)."""
    if len(archive_snapshots) < 2:
        return []
    points: list[ArchiveTurnoverPoint] = []
    for step in range(1, len(archive_snapshots)):
        before = set(archive_snapshots[step - 1])
        after = set(archive_snapshots[step])
        points.append(
            ArchiveTurnoverPoint(
                step=step, entered=frozenset(after - before), left=frozenset(before - after)
            )
        )
    return points
