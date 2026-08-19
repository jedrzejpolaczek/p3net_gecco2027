"""
Surrogate quality: rank correlation vs |H_t|.

Two quality metrics, matching the two surrogate shapes in this paper:

- `rank_correlation` (Spearman/Kendall) for a regression-style surrogate
  predicting an absolute value (p3net.surrogates.absolute_regressor).
- `pairwise_comparison_accuracy` for a relational surrogate predicting
  pairwise differences (p3net.surrogates.relative_linkage_aware's
  delta_hat_F) -- rank correlation doesn't directly apply to a surrogate
  that never predicts an absolute value, so quality here is "did the
  predicted delta's sign agree with the true delta's sign".

`surrogate_quality_trace` tracks rank_correlation as a function of |H_t|
by refitting an absolute-style surrogate on growing prefixes of the
observation history -- this feeds the kappa / acceptance-threshold
sensitivity analysis (configs/experiment/kappa_threshold_sweep.yaml),
which reports surrogate rank correlation jointly with fixed-budget
hypervolume (p3net.metrics.hypervolume).

Reference: chapters/v003/results/main.tex ("Metrics", "Surrogate error
accumulation (kappa and acceptance threshold)").
"""

from __future__ import annotations

from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import Protocol

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype
from scipy.stats import kendalltau, spearmanr


def rank_correlation(
    predicted: Sequence[float], true: Sequence[float], *, method: str = "spearman"
) -> float:
    if len(predicted) != len(true):
        raise ValueError("predicted and true must have the same length")
    if len(predicted) < 2:
        raise ValueError("rank correlation needs at least 2 points")
    if method == "spearman":
        statistic, _ = spearmanr(predicted, true)
    elif method == "kendall":
        statistic, _ = kendalltau(predicted, true)
    else:
        raise ValueError(
            f"unknown rank correlation method {method!r}, expected 'spearman' or 'kendall'"
        )
    return float(statistic)


def pairwise_comparison_accuracy(
    predicted_deltas: Sequence[float], true_deltas: Sequence[float]
) -> float:
    """Fraction of pairs where the predicted delta's sign agrees with the
    true delta's sign (0.0 counted as nonnegative on both sides) -- the
    quality metric for a *relative* surrogate, which has no absolute
    prediction for rank_correlation to compare."""
    if len(predicted_deltas) != len(true_deltas):
        raise ValueError("predicted_deltas and true_deltas must have the same length")
    if not predicted_deltas:
        raise ValueError("need at least one pair")
    agreements = sum(1 for p, t in zip(predicted_deltas, true_deltas) if (p >= 0) == (t >= 0))
    return agreements / len(predicted_deltas)


def calibration_r2(predicted_deltas: Sequence[float], true_deltas: Sequence[float]) -> float:
    """Coefficient of determination between predicted and true delta
    magnitude -- a second, independent read on delta_hat_F's quality
    alongside pairwise_comparison_accuracy above, which only ever scores
    sign agreement and is blind to whether the *size* of a predicted
    improvement means anything. 1.0 is a perfect fit, 0.0 matches always
    predicting the mean true delta, and negative values (unlike the [0, 1]
    accuracy metric) are possible and mean worse than that constant
    baseline."""
    if len(predicted_deltas) != len(true_deltas):
        raise ValueError("predicted_deltas and true_deltas must have the same length")
    if not predicted_deltas:
        raise ValueError("need at least one pair")
    mean_true = sum(true_deltas) / len(true_deltas)
    ss_tot = sum((t - mean_true) ** 2 for t in true_deltas)
    if ss_tot == 0.0:
        raise ValueError(
            "calibration_r2 is undefined when every true_delta is identical "
            "(zero variance to explain)"
        )
    ss_res = sum((t - p) ** 2 for p, t in zip(predicted_deltas, true_deltas))
    return 1.0 - ss_res / ss_tot


class _AbsoluteSurrogate(Protocol):
    def fit(self, observations: list[Observation], *, objective_index: int = 0) -> None: ...
    def predict(self, genotype: Genotype) -> float: ...


@dataclass(frozen=True)
class SurrogateQualityPoint:
    history_size: int
    rank_correlation: float


def surrogate_quality_trace(
    observations: list[Observation],
    surrogate_factory: Callable[[], _AbsoluteSurrogate],
    *,
    objective_index: int = 0,
    min_history: int = 2,
    step: int = 1,
    method: str = "spearman",
) -> list[SurrogateQualityPoint]:
    """Refits a fresh absolute-style surrogate on the first k observations
    for k = min_history, min_history + step, ..., len(observations), and
    tracks in-sample rank correlation between its predictions and the true
    objective at each k -- the paper tracks surrogate fit quality over the
    course of search, not held-out generalisation, so training and scoring
    both use the same growing prefix."""
    if min_history < 2:
        raise ValueError("min_history must be at least 2 (rank correlation needs 2+ points)")
    points: list[SurrogateQualityPoint] = []
    for k in range(min_history, len(observations) + 1, step):
        history = observations[:k]
        surrogate = surrogate_factory()
        surrogate.fit(history, objective_index=objective_index)
        predicted = [surrogate.predict(obs.genotype) for obs in history]
        true = [obs.objectives[objective_index] for obs in history]
        points.append(
            SurrogateQualityPoint(
                history_size=k, rank_correlation=rank_correlation(predicted, true, method=method)
            )
        )
    return points
