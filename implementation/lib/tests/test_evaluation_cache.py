"""Tests for p3net.harness.evaluation_cache."""

import pytest

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.problem.genotype import Genotype


def test_cache_key_includes_genotype_experiment_type_and_protocol_version():
    cache = EvaluationCache()
    g = Genotype(values=("a", 1))
    cache.put(g, 0.5, experiment_type="p3net", protocol_version="v1")
    assert cache.has(g, experiment_type="p3net", protocol_version="v1")
    assert not cache.has(g, experiment_type="nsganetv2", protocol_version="v1")


def test_protocol_version_bump_invalidates_stale_entries():
    cache = EvaluationCache()
    g = Genotype(values=("a", 1))
    cache.put(g, 0.5, experiment_type="p3net", protocol_version="v1")
    assert not cache.has(g, experiment_type="p3net", protocol_version="v2")


def test_duplicate_genotype_lookup_is_uniform_regardless_of_caller():
    cache = EvaluationCache()
    g = Genotype(values=("a", 1))
    cache.put(g, 0.5, experiment_type="p3net", protocol_version="v1")
    assert cache.has(g, experiment_type="p3net", protocol_version="v1")
    assert cache.get(g, experiment_type="p3net", protocol_version="v1") == 0.5


def test_duplication_counted_at_proposal_time_independent_of_hit_miss():
    cache = EvaluationCache()
    g1 = Genotype(values=("a", 1))
    g2 = Genotype(values=("b", 2))

    assert cache.record_proposal(g1, experiment_type="p3net", protocol_version="v1") is False
    cache.put(g1, 0.1, experiment_type="p3net", protocol_version="v1")

    assert cache.record_proposal(g1, experiment_type="p3net", protocol_version="v1") is True
    assert cache.record_proposal(g2, experiment_type="p3net", protocol_version="v1") is False

    assert cache.duplication_rate == pytest.approx(1 / 3)


def test_empty_cache_duplication_rate_is_zero():
    cache = EvaluationCache()
    assert cache.duplication_rate == 0.0


def test_size_reflects_stored_entries():
    cache = EvaluationCache()
    cache.put(Genotype(values=("a",)), 1.0, experiment_type="p3net", protocol_version="v1")
    cache.put(Genotype(values=("b",)), 2.0, experiment_type="p3net", protocol_version="v1")
    assert cache.size() == 2
