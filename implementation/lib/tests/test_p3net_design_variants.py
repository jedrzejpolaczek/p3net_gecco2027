"""Restored design-decision ablation axes on P3Net (2026-09-13, review
finding P4). The behavioural guarantee that matters most -- defaults
reproduce the persisted p3net runs exactly -- is checked against real
benchmark data by experiments/scripts/verify_p3net_unchanged.py; these
tests pin the constructor contract and the Pyramid hook."""

from __future__ import annotations

import random

import pytest

from p3net.methods.p3net import P3Net
from p3net.problem.genotype import CategoricalDomain, SearchSpace
from p3net.search_engines.p3.pyramid import Pyramid
from sklearn.linear_model import LinearRegression


def _space() -> SearchSpace:
    return SearchSpace(domains=tuple(CategoricalDomain(values=("a", "b", "c")) for _ in range(4)))


def test_defaults_are_the_single_retained_behaviour():
    method = P3Net(search_space=_space(), validity=None, model_factory=LinearRegression, rng=random.Random(0))
    assert method.truncation == "pareto"
    assert method.stall_recovery == "reinject"
    assert method.donor_pool == "h_t_only"
    assert method.cascade is False


@pytest.mark.parametrize(
    "field,value",
    [("truncation", "bogus"), ("stall_recovery", "bogus"), ("donor_pool", "bogus")],
)
def test_unknown_strategy_values_are_rejected(field, value):
    with pytest.raises(ValueError):
        P3Net(search_space=_space(), validity=None, model_factory=LinearRegression, rng=random.Random(0), **{field: value})


def test_mark_stalled_forces_a_level_stalled():
    pyramid = Pyramid(growth_factor=2)
    pyramid.add_level()
    assert not pyramid.is_stalled(0)
    pyramid.mark_stalled(0)
    assert pyramid.is_stalled(0)
    assert pyramid.all_stalled
