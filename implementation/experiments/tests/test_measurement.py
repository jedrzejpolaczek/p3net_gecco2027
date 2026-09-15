"""Tests for measurement/: resource meter, simulated training cost, decision
quality metrics, and the decision log's reservoir sampling."""

from __future__ import annotations

import math
import random

import pytest
from p3net.harness.decision_log import DecisionLog
from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import Genotype

from measurement.decisions import confusion, decision_quality, simple_regret
from measurement.resources import ResourceMeter, TimedSubstrate
from measurement.training_cost import simulated_training_seconds
from methods.multi_fidelity import FidelityQuery


class _Substrate:
    def __init__(self):
        self.calls = 0

    def objectives(self, g):
        self.calls += 1
        return (1.0, 2.0)

    def max_epochs(self):
        return 10

    def training_seconds(self, g, epochs):
        return 3.0 * epochs


def test_timed_substrate_delegates_and_counts():
    inner = _Substrate()
    timed = TimedSubstrate(inner)
    with ResourceMeter(timed) as meter:
        assert timed.objectives(Genotype(values=(1,))) == (1.0, 2.0)
        assert timed.max_epochs() == 10
        sum(i * i for i in range(20000))
    resources = meter.as_dict()
    assert resources["benchmark_queries"] == 1 and inner.calls == 1
    assert resources["wall_seconds"] >= resources["benchmark_seconds"] >= 0
    assert resources["optimizer_seconds"] == pytest.approx(
        resources["wall_seconds"] - resources["benchmark_seconds"]
    )
    assert resources["process_peak_rss_mb"] > 0


def test_simulated_training_seconds_single_and_multi_fidelity():
    g1, g2 = Genotype(values=(1,)), Genotype(values=(2,))
    state = RunState(history=[Observation(g1, (0, 0)), Observation(g2, (0, 0))], evaluations_used=2)

    class SingleFidelity:
        pass

    assert simulated_training_seconds(_Substrate(), state, SingleFidelity()) == 60.0

    class MultiFidelity:
        fidelity_queries = [
            FidelityQuery(g1, 1, (0, 0), 0.1),
            FidelityQuery(g2, 1, (0, 0), 0.1),
            FidelityQuery(g1, 3, (0, 0), 0.2),
            FidelityQuery(g1, 10, (0, 0), 0.7),
        ]

    # g1 trained to 10 epochs (30 s, resumed from checkpoints), g2 to 1 epoch (3 s)
    assert simulated_training_seconds(_Substrate(), state, MultiFidelity()) == 33.0


def _record(accepted, true_improvement, threshold=0.0, predicted=0.0):
    return {
        "kind": "improvement",
        "source": "mixing",
        "accepted": accepted,
        "true_improvement": true_improvement,
        "threshold": threshold,
        "predicted": predicted,
    }


def test_confusion_counts_and_derived_measures():
    records = (
        [_record(True, 1.0)] * 3  # TP
        + [_record(True, -1.0)] * 1  # FP
        + [_record(False, -1.0)] * 4  # TN
        + [_record(False, 0.5)] * 2  # FN
    )
    c = confusion(records)
    assert (c["tp"], c["fp"], c["tn"], c["fn"]) == (3, 1, 4, 2)
    assert c["precision"] == pytest.approx(0.75)
    assert c["recall"] == pytest.approx(0.6)
    assert c["fpr"] == pytest.approx(0.2)
    assert c["balanced_accuracy"] == pytest.approx((0.6 + 0.8) / 2)
    assert c["mcc"] == pytest.approx((3 * 4 - 1 * 2) / math.sqrt(4 * 5 * 5 * 6))


def test_threshold_is_part_of_the_real_label():
    assert confusion([_record(True, 0.5, threshold=1.0)])["fp"] == 1


def test_decision_quality_groups_by_source_and_ranks():
    records = [_record(i % 2 == 0, float(i), predicted=float(i)) for i in range(10)]
    quality = decision_quality(records)
    assert quality["mixing"]["rank"]["spearman"] == pytest.approx(1.0)
    assert sum(b["n"] for b in quality["mixing"]["calibration"]) == 10


def test_simple_regret_is_monotone():
    assert simple_regret([5.0, 3.0, 4.0, 1.0], 1.0) == [4.0, 2.0, 2.0, 0.0]


def test_decision_log_reservoir_is_bounded_and_uniform():
    counts = [0] * 100
    for trial in range(400):
        log = DecisionLog(limit=10, seed=trial)
        for i in range(100):
            log.selection(
                source="s", candidate=Genotype(values=(i,)), predicted_f1=0.0, accepted=True
            )
        assert len(log.records) == 10 and log.offered == 100
        for r in log.records:
            counts[r["candidate"][0]] += 1
    # every decision is kept with probability 0.1, i.e. ~40 times in 400 trials
    assert min(counts) > 15 and max(counts) < 70


def test_decision_log_does_not_touch_the_global_random_state():
    random.seed(5)
    expected = random.random()
    random.seed(5)
    log = DecisionLog(limit=1)
    for i in range(50):
        log.selection(source="s", candidate=Genotype(values=(i,)), predicted_f1=0.0, accepted=False)
    assert random.random() == expected
