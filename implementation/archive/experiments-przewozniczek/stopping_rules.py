"""Concrete StoppingRule implementations for this paper's experiment,
satisfying the p3net.harness.runner.StoppingRule protocol."""

from __future__ import annotations

from dataclasses import dataclass, field

from p3net.harness.runner import RunState, budget_exhausted


@dataclass
class ExplorationCollapse:
    """Stops early if the population has collapsed to very few distinct
    genotypes within a recent window of full evaluations -- analogous to
    the criterion bartnik2026evolutionary needed for NAS-Bench-201-scale
    spaces, where a small search space can converge (or exhaust its
    genuinely distinct points) well before the evaluation budget runs out.
    """

    window: int = 20
    min_unique_fraction: float = 0.2

    def __call__(self, state: RunState, *, budget: int) -> bool:
        if len(state.history) < self.window:
            return False
        recent = state.history[-self.window :]
        unique = len({obs.genotype for obs in recent})
        return (unique / self.window) < self.min_unique_fraction


@dataclass
class BudgetOrExplorationCollapse:
    """Composes the library's default budget-exhaustion rule with
    ExplorationCollapse: stop when EITHER fires (Results: "a stopping rule
    covering both the evaluation budget and... an exploration collapse
    criterion")."""

    exploration_collapse: ExplorationCollapse = field(default_factory=ExplorationCollapse)

    def __call__(self, state: RunState, *, budget: int) -> bool:
        return budget_exhausted(state, budget=budget) or self.exploration_collapse(
            state, budget=budget
        )
