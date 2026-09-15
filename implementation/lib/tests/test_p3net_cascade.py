"""Tests for P3Net's cascade=True mode (every pyramid level live) and the
in-batch deduplication it needs.

cascade=True was restored on 2026-09-13 from the 2026-08-16 ablation code
and until now was only checked to run. It became the candidate final form
of P3Net, so its two defining properties are pinned directly here, plus a
regression test for the duplicate-evaluation bug found in the real grid
(70 duplicate full evaluations across 61 of 480 runs)."""

from __future__ import annotations

import random

import pytest
from sklearn.linear_model import LinearRegression

from p3net.harness.evaluation_cache import EvaluationCache
from p3net.harness.runner import Runner
from p3net.methods.p3net import P3Net
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace


def _always_valid(genotype: Genotype) -> float:
    return -1.0


def _objective(genotype: Genotype):
    ones = sum(1 for v in genotype.values if v == 1)
    return (-float(ones), float(sum(genotype.values)))


def _method(space: SearchSpace, *, cascade: bool, seed: int = 0) -> P3Net:
    return P3Net(
        search_space=space,
        validity=_always_valid,
        model_factory=LinearRegression,
        rng=random.Random(seed),
        cascade=cascade,
        analytic_cost=lambda g: _objective(g),
    )


# -- EvaluationCache.record_proposal(pending=...) ----------------------------


def test_record_proposal_treats_pending_genotypes_as_duplicates():
    cache = EvaluationCache()
    g = Genotype(values=(1, 0))
    assert cache.record_proposal(g, experiment_type="t", protocol_version="v") is False
    assert cache.record_proposal(g, experiment_type="t", protocol_version="v", pending={g}) is True
    assert cache.duplication_rate == pytest.approx(0.5)


def test_record_proposal_default_is_unchanged():
    cache = EvaluationCache()
    g = Genotype(values=(1, 0))
    assert cache.record_proposal(g, experiment_type="t", protocol_version="v") is False
    cache.put(g, (0.0,), experiment_type="t", protocol_version="v")
    assert cache.record_proposal(g, experiment_type="t", protocol_version="v") is True


# -- the two defining properties of cascade ------------------------------------


def test_every_level_proposes_once_multiple_levels_exist():
    space = SearchSpace(domains=(CategoricalDomain(values=(0, 1, 2)),) * 8)
    method = _method(space, cascade=True, seed=3)
    runner = Runner(objective=_objective, budget=120)

    levels_in_last_batch: list[set[int]] = []
    original_propose = method.propose

    def spying_propose(state):
        before = dict(method._pending_level)
        proposals = original_propose(state)
        levels_in_last_batch.append({method._pending_level[g] for g in proposals if g not in before})
        return proposals

    method.propose = spying_propose  # type: ignore[method-assign]
    runner.run(method)

    assert len(method._pyramid.levels) >= 2, "test needs the pyramid to grow to be meaningful"
    multi_level_batches = [s for s in levels_in_last_batch if len(s) >= 2]
    assert multi_level_batches, "no batch ever drew proposals from more than one level"


def test_observations_are_routed_back_to_the_level_that_proposed_them():
    space = SearchSpace(domains=(CategoricalDomain(values=(0, 1, 2)),) * 8)
    method = _method(space, cascade=True, seed=5)
    runner = Runner(objective=_objective, budget=120)

    routed_correctly = True
    original_update = method._update_level_population

    def spying_update(level, level_index, new_observations):
        nonlocal routed_correctly
        for obs in new_observations:
            proposer = proposal_level.get(obs.genotype)
            if proposer is not None and proposer != level_index:
                routed_correctly = False
        return original_update(level, level_index, new_observations)

    proposal_level: dict[Genotype, int] = {}
    original_propose = method.propose

    def spying_propose(state):
        proposals = original_propose(state)
        for g in proposals:
            if g in method._pending_level:
                proposal_level[g] = method._pending_level[g]
        return proposals

    method.propose = spying_propose  # type: ignore[method-assign]
    method._update_level_population = spying_update  # type: ignore[method-assign]
    runner.run(method)

    assert len(method._pyramid.levels) >= 2
    assert routed_correctly
    # Only the final batch may leave entries behind: the Runner truncates a
    # batch that would overrun the budget, so those proposals are never
    # evaluated and never routed.
    evaluated = {obs.genotype for obs in method._history.values()}
    assert not (set(method._pending_level) & evaluated), "an evaluated genotype was never routed"


# -- regression: no duplicate full evaluations ---------------------------------


@pytest.mark.parametrize("seed", range(12))
def test_cascade_never_evaluates_the_same_genotype_twice(seed):
    """A deliberately tiny space (3^5 = 243 genotypes) and a large budget make
    two levels proposing the same not-yet-evaluated genotype in one batch
    very likely -- exactly the condition that produced duplicates before
    the in-batch `pending` check."""
    space = SearchSpace(domains=(CategoricalDomain(values=(0, 1, 2)),) * 5)
    method = _method(space, cascade=True, seed=seed)
    state = Runner(objective=_objective, budget=150).run(method)
    evaluated = [g for g in (obs.genotype for obs in state.history)]
    assert len(evaluated) == len(set(evaluated))


@pytest.mark.parametrize("seed", range(6))
def test_default_mode_never_evaluates_the_same_genotype_twice(seed):
    space = SearchSpace(domains=(CategoricalDomain(values=(0, 1, 2)),) * 5)
    method = _method(space, cascade=False, seed=seed)
    state = Runner(objective=_objective, budget=150).run(method)
    evaluated = [obs.genotype for obs in state.history]
    assert len(evaluated) == len(set(evaluated))
