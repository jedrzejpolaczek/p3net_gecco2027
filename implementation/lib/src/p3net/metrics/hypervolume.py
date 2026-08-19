"""Hypervolume indicator over an arbitrary objective front."""

from __future__ import annotations

from collections.abc import Sequence
from itertools import combinations

from p3net.problem.objectives import Objectives, pareto_front


def nadir_point(points: Sequence[Objectives]) -> Objectives:
    """Componentwise maximum (minimisation: the worst value seen in each
    objective) -- a hypervolume reference point that is, by construction,
    weakly worse than every one of `points` in every objective, so
    `hypervolume(points, reference=nadir_point(points))` never raises.
    Used by Pyramid.promote's hypervolume-contribution stall criterion
    (2026-08-18) to get a valid reference without needing one supplied
    from outside."""
    if not points:
        raise ValueError("nadir_point needs at least one point")
    dims = len(points[0])
    return tuple(max(p[j] for p in points) for j in range(dims))


def hypervolume(points: Sequence[Objectives], reference: Objectives) -> float:
    """Hypervolume dominated by `points` (minimisation) relative to a
    reference point that must be weakly worse than every point in every
    objective. Generic in the number of objectives.

    Two objectives (this project's actual usage -- f1, f2 throughout):
    exact, via an O(n log n) sort-and-sweep over the nondominated front,
    which scales to realistic front sizes (verified against real
    experiment data with a pooled best-known front of 70-140 points --
    the inclusion-exclusion path below could not complete on fronts that
    size at all, let alone quickly).

    Three or more objectives: exact, via inclusion-exclusion over the
    nondominated subset of `points` -- O(2^k) in the number of
    nondominated points k. Only reachable if this library or a caller
    ever scores a 3+-objective front; fine for small k, not intended for
    large ones. A dedicated 3+-D algorithm (e.g. WFG) is future work if
    that ever becomes the common case rather than the 2-objective one.
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

    if dims == 2:
        return _hypervolume_2d(front, reference)
    return _hypervolume_inclusion_exclusion(front, reference, dims)


def _hypervolume_2d(front: list[Objectives], reference: Objectives) -> float:
    """Sort-and-sweep hypervolume for a 2-objective nondominated front:
    O(n log n). On a true Pareto front under minimisation, sorting by the
    first objective ascending also sorts the second objective descending
    (a tie or reversal would mean one point dominates the other), so each
    point's rectangle spans horizontally from its own f1 up to the next
    point's f1 (or the reference, for the last point) and vertically from
    its own f2 up to the reference -- these rectangles are disjoint, so
    the total hypervolume is just their sum, no inclusion-exclusion
    needed."""
    ordered = sorted(front, key=lambda p: p[0])
    total = 0.0
    for i, p in enumerate(ordered):
        next_f1 = ordered[i + 1][0] if i + 1 < len(ordered) else reference[0]
        width = next_f1 - p[0]
        height = reference[1] - p[1]
        total += width * height
    return total


def _hypervolume_inclusion_exclusion(
    front: list[Objectives], reference: Objectives, dims: int
) -> float:
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
