"""Tests for experiments.metrics (surrogate_quality, diagnostics).

Reference: experiments/metrics/*; chapters/v003/results/main.tex
("Metrics", "Diagnostics").
"""

import random

import pytest
from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Observation
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace
from p3net.surrogates.absolute_regressor import AbsoluteRegressorSurrogate
from sklearn.linear_model import LinearRegression

from metrics.diagnostics import archive_turnover, duplication_rate
from metrics.surrogate_quality import (
    pairwise_comparison_accuracy,
    rank_correlation,
    surrogate_quality_trace,
)

# -- surrogate_quality --------------------------------------------------


def test_rank_correlation_is_perfect_for_identical_orderings():
    assert rank_correlation([1.0, 2.0, 3.0, 4.0], [10.0, 20.0, 30.0, 40.0]) == pytest.approx(1.0)


def test_rank_correlation_is_perfectly_negative_for_reversed_orderings():
    assert rank_correlation([1.0, 2.0, 3.0, 4.0], [40.0, 30.0, 20.0, 10.0]) == pytest.approx(-1.0)


def test_rank_correlation_supports_kendall_too():
    value = rank_correlation([1.0, 2.0, 3.0, 4.0], [10.0, 20.0, 30.0, 40.0], method="kendall")
    assert value == pytest.approx(1.0)


def test_rank_correlation_rejects_mismatched_lengths():
    with pytest.raises(ValueError):
        rank_correlation([1.0, 2.0], [1.0])


def test_rank_correlation_rejects_unknown_method():
    with pytest.raises(ValueError):
        rank_correlation([1.0, 2.0], [1.0, 2.0], method="pearson")


def test_pairwise_comparison_accuracy_counts_sign_agreement():
    predicted_deltas = [1.0, -1.0, 1.0]
    true_deltas = [1.0, -1.0, -1.0]
    assert pairwise_comparison_accuracy(predicted_deltas, true_deltas) == pytest.approx(2 / 3)


def test_pairwise_comparison_accuracy_perfect_agreement():
    assert pairwise_comparison_accuracy([1.0, -2.0, 0.0], [5.0, -0.5, 0.0]) == pytest.approx(1.0)


def test_pairwise_comparison_accuracy_rejects_empty_input():
    with pytest.raises(ValueError):
        pairwise_comparison_accuracy([], [])


_WEIGHTS = (
    1,
    2,
    4,
    8,
    16,
    32,
)  # distinct powers of two -> every 6-bit genotype maps to a unique sum


def _linear_observations() -> list[Observation]:
    space = SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * 6)
    rng = random.Random(0)
    seen: set[Genotype] = set()
    observations = []
    while len(observations) < 12:
        g = space.sample_uniform(rng)
        if g in seen:
            continue
        seen.add(g)
        objective = float(sum(w * v for w, v in zip(_WEIGHTS, g.values)))
        observations.append(Observation(genotype=g, objectives=(objective,)))
    return observations


def test_surrogate_quality_trace_tracks_rank_correlation_as_history_grows():
    observations = _linear_observations()
    trace = surrogate_quality_trace(
        observations,
        lambda: AbsoluteRegressorSurrogate(model_factory=LinearRegression),
        min_history=4,
        step=2,
    )
    assert [point.history_size for point in trace] == [4, 6, 8, 10, 12]
    # A linear model on one-hot features can fit a linear sum objective
    # essentially exactly once there's enough data -- the final, largest
    # prefix should show a near-perfect in-sample rank correlation.
    assert trace[-1].rank_correlation == pytest.approx(1.0, abs=1e-6)


def test_surrogate_quality_trace_rejects_too_small_min_history():
    observations = _linear_observations()
    with pytest.raises(ValueError):
        surrogate_quality_trace(
            observations,
            lambda: AbsoluteRegressorSurrogate(model_factory=LinearRegression),
            min_history=1,
        )


# -- diagnostics ----------------------------------------------------------


def test_duplication_rate_is_counted_at_proposal_time_not_evaluation_time():
    cache = EvaluationCache()
    g1 = Genotype(values=(0, 0))
    g2 = Genotype(values=(0, 1))

    # First proposal of each genotype is not a duplicate.
    assert cache.record_proposal(g1, experiment_type="t", protocol_version="v1") is False
    assert cache.record_proposal(g2, experiment_type="t", protocol_version="v1") is False
    assert duplication_rate(cache) == pytest.approx(0.0)

    # g1 hasn't actually been evaluated (put) yet -- record_proposal still
    # correctly reports it as a fresh proposal, not a duplicate, because
    # duplication is about repeated PROPOSALS, not repeated evaluations.
    cache.put(g1, (1.0,), experiment_type="t", protocol_version="v1")

    # Proposing g1 again now IS a duplicate (it's in H_t).
    assert cache.record_proposal(g1, experiment_type="t", protocol_version="v1") is True
    assert duplication_rate(cache) == pytest.approx(1 / 3)


def test_duplication_rate_is_a_thin_readthrough_of_the_cache():
    cache = EvaluationCache()
    g = Genotype(values=(0, 0))
    cache.record_proposal(g, experiment_type="t", protocol_version="v1")
    assert duplication_rate(cache) == cache.duplication_rate


def test_archive_turnover_reports_entries_and_exits_per_step():
    g1, g2, g3, g4 = (Genotype(values=(i,)) for i in range(4))
    snapshots = [
        [g1, g2],
        [g1, g2, g3],  # g3 entered
        [g1, g3, g4],  # g2 left, g4 entered
    ]
    turnover = archive_turnover(snapshots)
    assert len(turnover) == 2
    assert turnover[0].step == 1
    assert turnover[0].entered == frozenset({g3})
    assert turnover[0].left == frozenset()
    assert turnover[1].step == 2
    assert turnover[1].entered == frozenset({g4})
    assert turnover[1].left == frozenset({g2})


def test_archive_turnover_handles_fewer_than_two_snapshots():
    assert archive_turnover([]) == []
    assert archive_turnover([[Genotype(values=(0,))]]) == []
