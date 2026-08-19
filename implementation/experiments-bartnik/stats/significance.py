"""
Statistical comparison: paired Wilcoxon signed-rank + Holm-Bonferroni +
effect size.

Implements paired Wilcoxon signed-rank tests for exactly the defined
comparison set -- P3Net vs. each of the other nine arms, per benchmark and
per budget tier -- NOT every pairwise combination among all arms/
baselines (the correction count in holm_bonferroni_correction depends on
this scope being right). An effect size (Cliff's delta) is reported
alongside every corrected p-value, not optional. This is intentionally
stricter than bartnik2026evolutionary's uncorrected comparisons with no
effect size -- a deliberate methodological choice, not something to
"simplify away".

Reference: chapters/v003/results/main.tex ("Statistical plan");
chapters/v003/notes/main.tex ("Comparison set for correction").
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass

from scipy.stats import wilcoxon


def cliffs_delta(a: Sequence[float], b: Sequence[float]) -> float:
    """Cliff's delta effect size: (P(a > b) - P(a < b)) over all pairs,
    in [-1, 1]. 0 means the two samples are stochastically
    indistinguishable; +-1 means every pair in one sample beats every
    pair in the other."""
    if not a or not b:
        raise ValueError("cliffs_delta needs at least one value in each sample")
    greater = sum(1 for x in a for y in b if x > y)
    less = sum(1 for x in a for y in b if x < y)
    return (greater - less) / (len(a) * len(b))


@dataclass(frozen=True)
class HolmResult:
    p_value: float
    adjusted_p_value: float
    reject_null: bool


def holm_bonferroni_correction(
    p_values: Sequence[float], *, alpha: float = 0.05
) -> list[HolmResult]:
    """Holm-Bonferroni step-down correction. Returns one HolmResult per
    input p-value, in the SAME order as the input (not sorted) -- the
    adjusted p-value is the standard Holm formula: for the i-th smallest
    raw p-value p_(i) among m tests, adjusted_(i) = max_{j<=i}
    min(1, (m-j+1) * p_(j)), enforced monotone nondecreasing via a running
    max over the sorted order (matches R's p.adjust(method="holm"))."""
    m = len(p_values)
    if m == 0:
        return []
    order = sorted(range(m), key=lambda i: p_values[i])
    adjusted = [0.0] * m
    running_max = 0.0
    for rank, i in enumerate(order):
        raw_adjusted = min(1.0, (m - rank) * p_values[i])
        running_max = max(running_max, raw_adjusted)
        adjusted[i] = running_max
    return [
        HolmResult(
            p_value=p_values[i], adjusted_p_value=adjusted[i], reject_null=adjusted[i] <= alpha
        )
        for i in range(m)
    ]


@dataclass(frozen=True)
class Comparison:
    """One entry in the defined comparison set: P3Net vs. one other arm,
    for one benchmark and one budget tier. p3net_scores/baseline_scores
    are paired (same run seed at the same index in both) -- required by
    the paired Wilcoxon signed-rank test."""

    baseline: str
    benchmark: str
    budget: int
    p3net_scores: tuple[float, ...]
    baseline_scores: tuple[float, ...]


@dataclass(frozen=True)
class ComparisonResult:
    comparison: Comparison
    p_value: float
    adjusted_p_value: float
    reject_null: bool
    effect_size: float


def compare_p3net_to_baselines(
    comparisons: list[Comparison], *, alpha: float = 0.05
) -> list[ComparisonResult]:
    if not comparisons:
        return []
    p_values: list[float] = []
    effect_sizes: list[float] = []
    for comparison in comparisons:
        if len(comparison.p3net_scores) != len(comparison.baseline_scores):
            raise ValueError(
                f"paired comparison requires equal-length paired samples "
                f"({comparison.baseline}/{comparison.benchmark}/budget{comparison.budget})"
            )
        _, p_value = wilcoxon(comparison.p3net_scores, comparison.baseline_scores)
        p_values.append(float(p_value))
        effect_sizes.append(cliffs_delta(comparison.p3net_scores, comparison.baseline_scores))

    holm_results = holm_bonferroni_correction(p_values, alpha=alpha)
    return [
        ComparisonResult(
            comparison=comparison,
            p_value=holm.p_value,
            adjusted_p_value=holm.adjusted_p_value,
            reject_null=holm.reject_null,
            effect_size=effect_size,
        )
        for comparison, holm, effect_size in zip(comparisons, holm_results, effect_sizes)
    ]
