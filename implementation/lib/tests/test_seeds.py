"""Tests for p3net.harness.seeds -- R vs s seed policy. (Gap in the
original task list -- adding it since SeedPolicy has real validation
logic.)"""

import pytest

from p3net.harness.seeds import SeedPolicy


def test_r_is_the_number_of_run_seeds():
    policy = SeedPolicy(run_seeds=(1, 2, 3))
    assert policy.r == 3


def test_s_defaults_to_one_and_is_distinct_from_r():
    policy = SeedPolicy(run_seeds=(1, 2, 3))
    assert policy.s == 1
    assert policy.s != policy.r


def test_rejects_empty_seed_list():
    with pytest.raises(ValueError):
        SeedPolicy(run_seeds=())


def test_rejects_duplicate_seeds():
    with pytest.raises(ValueError):
        SeedPolicy(run_seeds=(1, 1, 2))


def test_rejects_s_below_one():
    with pytest.raises(ValueError):
        SeedPolicy(run_seeds=(1, 2), s=0)
