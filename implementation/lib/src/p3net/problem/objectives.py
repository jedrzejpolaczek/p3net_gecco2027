"""Generic multi-objective machinery: Pareto dominance/front, fidelity
ladder, evaluation-noise handling."""

from __future__ import annotations

import statistics
from collections.abc import Callable, Sequence
from dataclasses import dataclass
from typing import TypeVar

Objectives = tuple[float, ...]

T = TypeVar("T")


def dominates(a: Objectives, b: Objectives) -> bool:
    """True iff a Pareto-dominates b (minimisation): a <= b in every
    objective and a < b in at least one."""
    if len(a) != len(b):
        raise ValueError("objective vectors must have the same length")
    return all(ai <= bi for ai, bi in zip(a, b)) and any(ai < bi for ai, bi in zip(a, b))


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


def fast_nondominated_sort(
    items: Sequence[T], objectives: Callable[[T], Objectives]
) -> list[list[T]]:
    """Standard NSGA-II fast nondominated sort: partitions items into ranked
    fronts (front 0 = nondominated, front 1 = dominated only by members of
    front 0, etc.). Generic library-level counterpart of
    experiments/search_engines/nsga2/nondominated_sort.py's textbook
    implementation -- kept here, not imported from there, so this library
    package never depends on the downstream experiments package."""
    n = len(items)
    scored = [objectives(item) for item in items]
    domination_counts = [0] * n
    dominated_indices: list[list[int]] = [[] for _ in range(n)]
    fronts: list[list[int]] = [[]]

    for p in range(n):
        for q in range(n):
            if p == q:
                continue
            if dominates(scored[p], scored[q]):
                dominated_indices[p].append(q)
            elif dominates(scored[q], scored[p]):
                domination_counts[p] += 1
        if domination_counts[p] == 0:
            fronts[0].append(p)

    i = 0
    while fronts[i]:
        next_front: list[int] = []
        for p in fronts[i]:
            for q in dominated_indices[p]:
                domination_counts[q] -= 1
                if domination_counts[q] == 0:
                    next_front.append(q)
        i += 1
        fronts.append(next_front)
    fronts.pop()  # the loop always appends one trailing empty front

    return [[items[idx] for idx in front] for front in fronts]


def crowding_distance(
    front: Sequence[T], objectives: Callable[[T], Objectives]
) -> dict[int, float]:
    """Standard NSGA-II crowding distance within one front (a single rank
    from fast_nondominated_sort): for each objective, sort by that objective
    and accumulate the normalised distance to neighbours; boundary points
    (best/worst per objective) get infinite distance so they are always kept
    when trimming to population size. Returns a mapping from `front`'s index
    to its distance, not item -> distance, since items need not be hashable
    or unique."""
    n = len(front)
    if n == 0:
        return {}
    scored = [objectives(item) for item in front]
    n_objectives = len(scored[0])
    distances = [0.0] * n

    for m in range(n_objectives):
        order = sorted(range(n), key=lambda i: scored[i][m])
        distances[order[0]] = float("inf")
        distances[order[-1]] = float("inf")
        obj_span = scored[order[-1]][m] - scored[order[0]][m]
        if obj_span == 0:
            continue
        for k in range(1, n - 1):
            distances[order[k]] += (scored[order[k + 1]][m] - scored[order[k - 1]][m]) / obj_span

    return {i: distances[i] for i in range(n)}


def select_survivors(
    items: Sequence[T], objectives: Callable[[T], Objectives], target_size: int
) -> list[T]:
    """mu+lambda elitist multi-objective survivor selection: nondominated
    sort, fill fronts until exceeding capacity, then trim the last admitted
    front by crowding distance. The generic building block every
    population-truncating method in this project should reduce a
    too-large population with, instead of an ad hoc single-objective sort
    that would silently discard nondominated points."""
    fronts = fast_nondominated_sort(items, objectives)
    survivors: list[T] = []
    for front in fronts:
        if len(survivors) + len(front) <= target_size:
            survivors.extend(front)
            continue
        distances = crowding_distance(front, objectives)
        ranked = sorted(range(len(front)), key=lambda i: distances[i], reverse=True)
        remaining = target_size - len(survivors)
        survivors.extend(front[i] for i in ranked[:remaining])
        break
    return survivors


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
