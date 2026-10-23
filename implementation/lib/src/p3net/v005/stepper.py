"""Ask-tell wrapper for methods that evaluate step by step (P3, eLyMPuS, MO-LS,
Bartnik): the algorithm is a generator that yields a genotype whenever it needs
real objectives and receives them back. The wrapper

- answers genotypes already in H_t from the cache, without proposing them (#35);
- proposes exactly one genotype per `propose` (interfaces §0);
- never proposes beyond the budget (K-2): when the budget is spent, `propose`
  returns [];
- keeps the elitist archive of real evaluations;
- forwards observer events (interfaces §7, Q-02).
"""

from __future__ import annotations

from collections.abc import Callable, Generator
from typing import Any

from p3net.harness.runner import Observation, RunState
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives
from p3net.v005.common import Budget, ElitistArchive, EvalCache, cardinalities, space_size

#: Consecutive cache hits after which a run is treated as exhausted (every genotype
#: the algorithm can still reach is already evaluated).
MAX_CACHED_IN_A_ROW = 200_000


class StepMethod:
    def __init__(
        self,
        space: SearchSpace,
        budget: int,
        rng,
        *,
        observer: Callable[[str, dict], None] | None = None,
    ):
        self.space = space
        self.domains = cardinalities(space)
        self.rng = rng
        self.budget = Budget(budget)
        self.cache = EvalCache()
        self.archive = ElitistArchive()
        self.observer = observer
        self.stop_reason: str | None = None
        self._gen: Generator[Genotype, Objectives, Any] | None = None
        self._pending: Genotype | None = None
        self._to_send: Objectives | None = None
        self._size = space_size(space)

    # -- to be provided by subclasses -------------------------------------------
    def _run(self) -> Generator[Genotype, Objectives, Any]:
        raise NotImplementedError

    # -- helpers for subclasses --------------------------------------------------
    def _emit(self, kind: str, **payload: Any) -> None:
        if self.observer is not None:
            self.observer(kind, payload)

    def _stop(self, reason: str) -> None:
        if self.stop_reason is None:
            self.stop_reason = reason
            self._emit("stop", reason=reason)

    # -- ask-tell -----------------------------------------------------------------
    def propose(self, state: RunState) -> list[Genotype]:
        if self.stop_reason is not None:
            return []
        if self._pending is not None:
            return [self._pending]
        if self._gen is None:
            self._gen = self._run()
            msg: Objectives | None = None
            first = True
        else:
            msg, first = self._to_send, False
        cached_in_a_row = 0
        while True:
            try:
                g = next(self._gen) if first else self._gen.send(msg)
            except StopIteration:
                self._stop("algorithm finished")
                return []
            first = False
            hit = self.cache.get(g)
            if hit is not None:
                msg = hit
                cached_in_a_row += 1
                if cached_in_a_row >= MAX_CACHED_IN_A_ROW or len(self.cache) >= self._size:
                    self._stop("exploration collapse: no unevaluated genotype reached")
                    return []
                continue
            if self.budget.used >= self.budget.total:
                self._stop("budget exhausted")
                return []
            self.budget.charge(g, self.cache)
            self._pending = g
            return [g]

    def update(self, state: RunState, new_observations: list[Observation]) -> None:
        for obs in new_observations:
            self.cache.put(obs.genotype, obs.objectives)
            self.archive.add(obs.objectives)
            if obs.genotype == self._pending:
                self._to_send = tuple(float(x) for x in obs.objectives)
                self._pending = None
