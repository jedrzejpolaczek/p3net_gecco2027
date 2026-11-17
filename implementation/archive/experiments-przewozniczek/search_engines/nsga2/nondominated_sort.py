"""NSGA-II nondominated sorting."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

from p3net.problem.objectives import Objectives, dominates

T = TypeVar("T")


def fast_nondominated_sort(
    items: Sequence[T], objectives: Callable[[T], Objectives]
) -> list[list[T]]:
    """Standard NSGA-II fast nondominated sort: partitions items into
    ranked fronts (front 0 = nondominated, front 1 = dominated only by
    members of front 0, etc.). Kept faithful to the textbook algorithm,
    unmodified, so any gain P3Net shows over an NSGA-II-based baseline is
    attributable to the search engine, not a weakened baseline (Results:
    "must not allow P3Net to be read as 'P3 plus Pareto filtering'").
    """
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
