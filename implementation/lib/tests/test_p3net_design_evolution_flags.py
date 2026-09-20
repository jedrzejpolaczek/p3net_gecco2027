"""Design Evolution stage flags on P3Net (restored 2026-09-14).

The early stages (S1, S2) are additionally verified against archived raw
runs bit for bit by experiments/scripts/verify_stage_reproduces_archive.py;
these tests pin the flags' contract and the one stage that has no archive
(S4', the reverted "start mixing sooner" attempt), whose documented symptom
is reproduced exactly."""

from __future__ import annotations

import random

import pytest
from sklearn.linear_model import LinearRegression

from p3net.harness.runner import Runner
from p3net.methods.p3net import P3Net
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace
from p3net.search_engines.p3.pyramid import Pyramid


def _space(n: int = 10) -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * n)


def _objective(genotype: Genotype):
    return (-float(sum(genotype.values)),)


def _method(**kwargs) -> P3Net:
    return P3Net(
        search_space=_space(),
        validity=lambda g: -1.0,
        model_factory=LinearRegression,
        rng=random.Random(kwargs.pop("seed", 3)),
        growth_factor=2,
        **kwargs,
    )


def test_defaults_are_the_current_engine():
    m = _method()
    assert (m.level_init, m.stall_criterion, m.bootstrap_threshold) == ("warm", "hypervolume", "level_size")


@pytest.mark.parametrize(
    "field,value", [("level_init", "x"), ("stall_criterion", "x"), ("bootstrap_threshold", "x")]
)
def test_unknown_values_are_rejected(field, value):
    with pytest.raises(ValueError):
        _method(**{field: value})


def test_dominance_criterion_requires_strict_dominance_of_the_incumbent():
    pyramid = Pyramid(growth_factor=2)
    pyramid.add_level()
    pyramid.levels[0].best_objectives = (1.0, 1.0)
    # a trade-off point: better on one objective, worse on the other
    trade_off = pyramid.promote(0, Genotype(values=(0,)), (0.5, 2.0), population_objectives=[(1.0, 1.0)], criterion="dominance")
    assert trade_off is False and pyramid.is_stalled(0)
    dominating = pyramid.promote(0, Genotype(values=(1,)), (0.5, 0.5), population_objectives=[(1.0, 1.0)], criterion="dominance")
    assert dominating is True and not pyramid.is_stalled(0)


def test_hypervolume_criterion_accepts_a_trade_off_point():
    pyramid = Pyramid(growth_factor=2)
    pyramid.add_level()
    pyramid.levels[0].best_objectives = (1.0, 1.0)
    assert pyramid.promote(0, Genotype(values=(0,)), (0.5, 2.0), population_objectives=[(1.0, 1.0)]) is True


def test_empty_level_init_never_warm_starts():
    method = _method(level_init="empty")
    calls = []
    original = method._warm_start_level
    method._warm_start_level = lambda level: calls.append(level) or original(level)  # type: ignore[method-assign]
    Runner(objective=_objective, budget=150).run(method)
    assert len(method._pyramid.levels) >= 2
    assert calls == []


def test_warm_level_init_warm_starts_every_grown_level():
    method = _method()
    calls = []
    original = method._warm_start_level
    method._warm_start_level = lambda level: calls.append(level) or original(level)  # type: ignore[method-assign]
    Runner(objective=_objective, budget=150).run(method)
    assert len(calls) == len(method._pyramid.levels) - 1


def test_eager_mixing_reproduces_the_documented_runaway_growth():
    """CHANGELOG, 2026-08-18: with the bootstrap threshold lowered to
    growth_factor, this exact setup (10 binary variables, OLS, seed 3,
    growth factor 2, budget 150) produced level_size_log entries of 2**96,
    versus a handful of levels for the retained engine.

    The runaway is asserted, not its exact exponent: the trajectory depends
    on the least-squares solutions, so the exponent differs between linear
    algebra backends (2**96 on Windows, 2**99 on Linux) while the behaviour
    -- level sizes exploding past anything a real run could hold -- does
    not."""
    eager = _method(bootstrap_threshold="growth_factor")
    Runner(objective=_objective, budget=150).run(eager)
    assert max(eager.level_size_log) > 2**40

    retained = _method()
    Runner(objective=_objective, budget=150).run(retained)
    assert max(retained.level_size_log) <= 2**9
