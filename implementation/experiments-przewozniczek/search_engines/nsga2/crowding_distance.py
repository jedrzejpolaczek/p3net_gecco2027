"""NSGA-II crowding-distance selection."""

from __future__ import annotations

from collections.abc import Callable, Sequence
from typing import TypeVar

from p3net.problem.objectives import Objectives

T = TypeVar("T")


def crowding_distance(
    front: Sequence[T], objectives: Callable[[T], Objectives]
) -> dict[int, float]:
    """Standard NSGA-II crowding distance within one front (a single rank
    from fast_nondominated_sort): for each objective, sort by that
    objective and accumulate the normalised distance to neighbours;
    boundary points (best/worst per objective) get infinite distance so
    they are always kept when trimming to population size. Returns a
    mapping from `front`'s index to its distance, not item -> distance,
    since items need not be hashable or unique.
    """
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
