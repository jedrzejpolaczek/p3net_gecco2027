"""Generic search-loop driver: budget accounting + pluggable stopping rule."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from typing import Protocol

from p3net.harness.seeds import SeedPolicy
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import Objectives


@dataclass(frozen=True)
class Observation:
    """One full evaluation: a (genotype, objective vector) pair -- the unit
    an H_t-style observation dataset is built from."""

    genotype: Genotype
    objectives: Objectives


@dataclass
class RunState:
    """Everything a StoppingRule needs to decide whether to stop: the
    observation history so far and how many full evaluations have been
    spent."""

    history: list[Observation] = field(default_factory=list)
    evaluations_used: int = 0


class StoppingRule(Protocol):
    def __call__(self, state: RunState, *, budget: int) -> bool: ...


def budget_exhausted(state: RunState, *, budget: int) -> bool:
    """Default StoppingRule: stop once the full-evaluation budget is
    spent."""
    return state.evaluations_used >= budget


class Method(Protocol):
    """The shape a runnable method must expose: propose the next batch of
    genotypes to fully evaluate, and update itself given their results."""

    def propose(self, state: RunState) -> list[Genotype]: ...

    def update(self, state: RunState, new_observations: list[Observation]) -> None: ...


@dataclass
class Runner:
    """Drives an arbitrary Method against an arbitrary full-evaluation
    objective for a fixed budget, using a pluggable StoppingRule. Counts
    cost exclusively in calls to the objective, never in calls to a
    surrogate the method may use internally."""

    objective: Callable[[Genotype], Objectives]
    budget: int
    stopping_rule: StoppingRule = budget_exhausted

    def run(self, method: Method) -> RunState:
        state = RunState()
        while not self.stopping_rule(state, budget=self.budget):
            proposals = method.propose(state)
            if not proposals:
                break
            remaining = self.budget - state.evaluations_used
            if remaining < len(proposals):
                proposals = proposals[:remaining]
            new_observations: list[Observation] = []
            for genotype in proposals:
                objectives = self.objective(genotype)
                observation = Observation(genotype=genotype, objectives=objectives)
                state.history.append(observation)
                state.evaluations_used += 1
                new_observations.append(observation)
            method.update(state, new_observations)
        return state

    def run_repeated(
        self, make_method: Callable[[int], Method], seed_policy: SeedPolicy
    ) -> list[RunState]:
        """Run R independent repetitions, one per seed in
        seed_policy.run_seeds, using an identical initialisation scheme
        (make_method(seed) must construct a freshly seeded Method each
        time)."""
        return [self.run(make_method(seed)) for seed in seed_policy.run_seeds]
