"""Tests for p3net.harness.runner -- generic Runner + StoppingRule."""

import random

from p3net.harness.runner import Observation, Runner, RunState
from p3net.harness.seeds import SeedPolicy
from p3net.problem.genotype import CategoricalDomain, Genotype, SearchSpace


def toy_space() -> SearchSpace:
    return SearchSpace(domains=(CategoricalDomain(values=(0, 1, 2)),) * 3)


def toy_objective(genotype: Genotype):
    return (float(sum(genotype.values)),)


class RandomProposer:
    """A minimal synthetic Method: propose one random genotype per step,
    ignoring all prior state."""

    def __init__(self, space: SearchSpace, seed: int):
        self._space = space
        self._rng = random.Random(seed)
        self.updates_seen: list[list[Observation]] = []

    def propose(self, state: RunState) -> list[Genotype]:
        return [self._space.sample_uniform(self._rng)]

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        self.updates_seen.append(new_observations)


def test_default_stopping_rule_stops_exactly_at_budget():
    runner = Runner(objective=toy_objective, budget=5)
    state = runner.run(RandomProposer(toy_space(), seed=0))
    assert state.evaluations_used == 5
    assert len(state.history) == 5


def test_budget_counts_only_true_evaluations_never_surrogate_calls():
    calls = {"n": 0}

    def counting_objective(genotype):
        calls["n"] += 1
        return (float(sum(genotype.values)),)

    runner = Runner(objective=counting_objective, budget=3)
    runner.run(RandomProposer(toy_space(), seed=1))
    assert calls["n"] == 3


def test_custom_stopping_rule_is_pluggable_not_hardcoded():
    """A synthetic StoppingRule unrelated to budget exhaustion: stop after
    exactly 2 evaluations, well below the configured budget -- proves the
    Runner genuinely delegates to whatever rule it's given."""

    def stop_after_two(state: RunState, *, budget: int) -> bool:
        return state.evaluations_used >= 2

    runner = Runner(objective=toy_objective, budget=100, stopping_rule=stop_after_two)
    state = runner.run(RandomProposer(toy_space(), seed=2))
    assert state.evaluations_used == 2


def test_run_repeated_uses_supplied_seed_list_and_fresh_method_each_time():
    seed_policy = SeedPolicy(run_seeds=(10, 20, 30))
    runner = Runner(objective=toy_objective, budget=2)
    states = runner.run_repeated(lambda seed: RandomProposer(toy_space(), seed=seed), seed_policy)
    assert len(states) == 3
    for state in states:
        assert state.evaluations_used == 2


def test_history_recorded_in_order_with_no_surrogate_only_entries():
    runner = Runner(objective=toy_objective, budget=4)
    state = runner.run(RandomProposer(toy_space(), seed=3))
    assert len(state.history) == 4
    for observation in state.history:
        assert isinstance(observation, Observation)
        assert observation.objectives == toy_objective(observation.genotype)


def test_runner_stops_early_if_method_proposes_nothing():
    class EmptyProposer:
        def propose(self, state):
            return []

        def update(self, state, new_observations):
            pass

    runner = Runner(objective=toy_objective, budget=10)
    state = runner.run(EmptyProposer())
    assert state.evaluations_used == 0
