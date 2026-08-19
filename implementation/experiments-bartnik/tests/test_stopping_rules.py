"""Tests for experiments.stopping_rules. (Gap in the original task list --
adding it.)"""

from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import Genotype

from stopping_rules import BudgetOrExplorationCollapse, ExplorationCollapse


def make_state(genotypes: list[Genotype]) -> RunState:
    history = [Observation(genotype=g, objectives=(0.0,)) for g in genotypes]
    return RunState(history=history, evaluations_used=len(history))


def test_fires_on_a_converged_population():
    rule = ExplorationCollapse(window=10, min_unique_fraction=0.2)
    genotypes = [Genotype(values=(0, 0))] * 10  # 1 unique genotype out of 10
    assert rule(make_state(genotypes), budget=1000) is True


def test_does_not_fire_on_a_diverse_population():
    rule = ExplorationCollapse(window=10, min_unique_fraction=0.2)
    genotypes = [Genotype(values=(i, i + 1)) for i in range(10)]  # all unique
    assert rule(make_state(genotypes), budget=1000) is False


def test_does_not_fire_before_window_is_full():
    rule = ExplorationCollapse(window=10, min_unique_fraction=0.2)
    genotypes = [Genotype(values=(0, 0))] * 3
    assert rule(make_state(genotypes), budget=1000) is False


def test_composed_rule_triggers_on_budget_exhaustion():
    rule = BudgetOrExplorationCollapse()
    genotypes = [Genotype(values=(i, i + 1)) for i in range(5)]
    assert rule(make_state(genotypes), budget=5) is True


def test_composed_rule_triggers_on_exploration_collapse():
    rule = BudgetOrExplorationCollapse(
        exploration_collapse=ExplorationCollapse(window=5, min_unique_fraction=0.5)
    )
    genotypes = [Genotype(values=(0, 0))] * 5
    assert rule(make_state(genotypes), budget=1000) is True  # budget far from exhausted


def test_composed_rule_does_not_trigger_when_neither_condition_holds():
    rule = BudgetOrExplorationCollapse(
        exploration_collapse=ExplorationCollapse(window=5, min_unique_fraction=0.5)
    )
    genotypes = [Genotype(values=(i, i + 1)) for i in range(5)]
    assert rule(make_state(genotypes), budget=1000) is False
