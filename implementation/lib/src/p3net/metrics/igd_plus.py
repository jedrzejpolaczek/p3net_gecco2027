"""Inverted Generational Distance plus (IGD+) against a known oracle
front."""

from __future__ import annotations

import math
from collections.abc import Sequence

from p3net.problem.objectives import Objectives


def igd_plus(
    approximation: Sequence[Objectives],
    oracle_front: Sequence[Objectives],
    *,
    normalise: bool = False,
) -> float:
    """IGD+ of `approximation` against a known, enumerable oracle Pareto
    front (minimisation). For each oracle point z, finds the closest
    approximation point using the IGD+ modified distance -- only counting
    how much an approximation point is WORSE than z in each objective, not
    how much better -- then averages over all oracle points.

    Only applicable where an exact oracle front exists; callers are
    responsible for that guard (Category 1 benchmarks only, per the
    paper's Category 1/2 classification) -- this module has no opinion on
    which benchmarks qualify.

    `normalise` rescales every objective to the oracle front's own
    [ideal, nadir] range before measuring distance. This matters whenever
    the objectives have different units: on NAS-HPO-Bench-II, f1 is a
    validation error in percent and f2 a training-and-validation time in
    seconds, and across that benchmark's exact oracle front f2 spans
    roughly 18 times the range f1 does -- so an unnormalised Euclidean
    distance is driven mostly by f2, and the accuracy objective the search
    is actually about contributes comparatively little. Normalising is
    the standard treatment for exactly this (an objective's scale is an
    arbitrary unit choice, not a statement about its importance).

    Defaults to False so existing callers and tests keep the textbook
    raw-scale definition; reporting code that compares across objectives
    with different units should pass True.
    """
    if not oracle_front:
        raise ValueError("oracle_front must be non-empty")
    if not approximation:
        raise ValueError("approximation must be non-empty")
    dims = len(oracle_front[0])
    if any(len(z) != dims for z in oracle_front) or any(len(a) != dims for a in approximation):
        raise ValueError("all points must share the same number of objectives")

    scale = [1.0] * dims
    if normalise:
        for j in range(dims):
            lo = min(z[j] for z in oracle_front)
            hi = max(z[j] for z in oracle_front)
            span = hi - lo
            # A degenerate objective (every oracle point identical on it)
            # carries no information about relative quality; leaving its
            # scale at 1.0 keeps it comparable in raw units rather than
            # dividing by zero.
            scale[j] = span if span > 0 else 1.0

    total = 0.0
    for z in oracle_front:
        best = min(
            math.sqrt(sum((max(0.0, a[j] - z[j]) / scale[j]) ** 2 for j in range(dims)))
            for a in approximation
        )
        total += best
    return total / len(oracle_front)
