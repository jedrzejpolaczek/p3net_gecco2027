"""Hypervolume indicator over an arbitrary objective front."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations

from p3net.problem.objectives import Objectives, pareto_front


def hypervolume(points: Sequence[Objectives], reference: Objectives) -> float:
    """Hypervolume dominated by `points` (minimisation) relative to a
    reference point that must be weakly worse than every point in every
    objective. Generic in the number of objectives. Exact, via
    inclusion-exclusion over the nondominated subset of `points` -- O(2^k)
    in the number of nondominated points k, fine for the point counts this
    library deals with; not intended for very large fronts.
    """
    if not points:
        return 0.0
    dims = len(reference)
    if any(len(p) != dims for p in points):
        raise ValueError("all points and the reference must share the same number of objectives")
    front = pareto_front(list(points), lambda p: p)
    for p in front:
        if any(p[j] > reference[j] for j in range(dims)):
            raise ValueError(
                "reference point must be weakly worse than every point in every objective"
            )

    total = 0.0
    n = len(front)
    for r in range(1, n + 1):
        sign = 1.0 if r % 2 == 1 else -1.0
        for subset in combinations(range(n), r):
            corner = [max(front[i][j] for i in subset) for j in range(dims)]
            volume = 1.0
            for j in range(dims):
                volume *= max(0.0, reference[j] - corner[j])
            total += sign * volume
    return total


def hypervolume_relative_to_best_known_front(
    points: Sequence[Objectives],
    best_known_front: Sequence[Objectives],
    reference: Objectives,
) -> float:
    """Hypervolume fallback for benchmarks with no enumerable oracle front:
    hypervolume(points) / hypervolume(best_known_front), both against the
    same reference point. Constructing `best_known_front` itself (e.g. the
    paper's own candidate definition: the union of all points evaluated by
    any compared method across all runs) is an experiments/-level concern,
    not this module's -- this function only computes the ratio given one.
    """
    points_hv = hypervolume(points, reference)
    best_hv = hypervolume(best_known_front, reference)
    if best_hv == 0.0:
        return 0.0
    return points_hv / best_hv
