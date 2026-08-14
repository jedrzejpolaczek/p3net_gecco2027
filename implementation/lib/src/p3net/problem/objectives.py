"""Generic multi-objective machinery: Pareto dominance/front, fidelity
ladder, evaluation-noise handling."""

from __future__ import annotations

import statistics
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypeVar

Objectives = tuple[float, ...]


def dominates(a: Objectives, b: Objectives) -> bool:
    """True iff a Pareto-dominates b (minimisation): a <= b in every
    objective and a < b in at least one."""
    if len(a) != len(b):
        raise ValueError("objective vectors must have the same length")
    return all(ai <= bi for ai, bi in zip(a, b)) and any(ai < bi for ai, bi in zip(a, b))


T = TypeVar("T")


def pareto_front(items: Sequence[T], objectives: Callable[[T], Objectives]) -> list[T]:
    """Return the nondominated subset of items, generic over any number of
    objectives and any item type (a Genotype, a run record, ...)."""
    scored = [(item, objectives(item)) for item in items]
    front: list[T] = []
    for item, item_obj in scored:
        if any(
            dominates(other_obj, item_obj)
            for other_item, other_obj in scored
            if other_item is not item
        ):
            continue
        front.append(item)
    return front


@dataclass(frozen=True)
class FidelityLevel:
    """One rung of a fidelity ladder: an opaque, ordered resource
    configuration. The library does not assume this packs "epochs"
    specifically -- a concrete problem may pack epochs, resolution, or
    anything else into `config`."""

    rank: int
    config: dict


@dataclass(frozen=True)
class FidelityLadder:
    levels: tuple[FidelityLevel, ...]

    def __post_init__(self) -> None:
        ranks = [lvl.rank for lvl in self.levels]
        if ranks != sorted(ranks):
            raise ValueError("fidelity levels must be given in increasing rank order")

    @property
    def highest(self) -> FidelityLevel:
        return self.levels[-1]


def evaluate_with_noise(
    query: Callable[[], float],
    *,
    s: int = 1,
    reduce: Callable[[Sequence[float]], float] | None = None,
) -> float:
    """Evaluate a possibly-stochastic query s times and reduce (median by
    default). A genuine no-op when s == 1 (deterministic substrates), not a
    special case -- still calls `query` exactly once and returns its value."""
    if s < 1:
        raise ValueError("s must be >= 1")
    values = [query() for _ in range(s)]
    if s == 1:
        return values[0]
    reducer = reduce if reduce is not None else statistics.median
    return reducer(values)
