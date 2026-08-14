"""Inverted Generational Distance plus (IGD+) against a known oracle
front."""

from __future__ import annotations

import math
from collections.abc import Sequence

from p3net.problem.objectives import Objectives


def igd_plus(approximation: Sequence[Objectives], oracle_front: Sequence[Objectives]) -> float:
    """IGD+ of `approximation` against a known, enumerable oracle Pareto
    front (minimisation). For each oracle point z, finds the closest
    approximation point using the IGD+ modified distance -- only counting
    how much an approximation point is WORSE than z in each objective, not
    how much better -- then averages over all oracle points.

    Only applicable where an exact oracle front exists; callers are
    responsible for that guard (Category 1 benchmarks only, per the
    paper's Category 1/2 classification) -- this module has no opinion on
    which benchmarks qualify.
    """
    if not oracle_front:
        raise ValueError("oracle_front must be non-empty")
    if not approximation:
        raise ValueError("approximation must be non-empty")
    dims = len(oracle_front[0])
    if any(len(z) != dims for z in oracle_front) or any(len(a) != dims for a in approximation):
        raise ValueError("all points must share the same number of objectives")

    total = 0.0
    for z in oracle_front:
        best = min(
            math.sqrt(sum(max(0.0, a[j] - z[j]) ** 2 for j in range(dims))) for a in approximation
        )
        total += best
    return total / len(oracle_front)
