"""Shared reporting internals: reading results/raw/*.json back into
Observation-based records, and the best-known-front/reference-point
construction that both tables.py (hypervolume-relative-to-best-known-front)
and plots.py (convergence, Pareto progression) need. Internal module, not
re-exported directly -- reporting/__init__.py re-exports the public names
from wherever they logically belong (best_known_front is credited to
plots.py, even though tables.py also consumes it from here).

Reference: chapters/v003/results/main.tex ("Metrics" paragraph -- the
best-known-front TODO).
"""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype
from p3net.problem.objectives import Objectives, pareto_front


@dataclass(frozen=True)
class RawRun:
    """One results/raw/*.json file, deserialised. `diagnostics` defaults
    to {} for older files persisted before scripts/run_experiment.py
    started recording it -- additive schema change, old files still
    readable."""

    method: str
    search_space: str
    budget: int
    seed: int
    evaluations_used: int
    history: tuple[Observation, ...]
    diagnostics: dict[str, Any] = field(default_factory=dict)

    @property
    def objectives(self) -> tuple[Objectives, ...]:
        return tuple(obs.objectives for obs in self.history)


def load_raw_run(path: Path) -> RawRun:
    payload = json.loads(path.read_text(encoding="utf-8"))
    history = tuple(
        Observation(
            genotype=Genotype(values=tuple(entry["genotype"])),
            objectives=tuple(entry["objectives"]),
        )
        for entry in payload["history"]
    )
    return RawRun(
        method=payload["method"],
        search_space=payload["search_space"],
        budget=payload["budget"],
        seed=payload["seed"],
        evaluations_used=payload["evaluations_used"],
        history=history,
        diagnostics=payload.get("diagnostics", {}),
    )


def load_raw_runs(results_dir: Path) -> list[RawRun]:
    """Every *.json under results_dir (scripts/run_experiment.py's
    results/raw/), in a stable (sorted-by-filename) order."""
    return [load_raw_run(p) for p in sorted(results_dir.glob("*.json"))]


def construct_best_known_front(runs: Sequence[RawRun]) -> list[Objectives]:
    """The candidate best-known front (chapters/v003/results/main.tex's
    own suggested definition): the Pareto front of the union of every
    point evaluated by any of the given runs, across every
    method/budget/seed passed in. Callers decide
    the pooling scope (e.g. "all runs of one benchmark, every budget tier
    and method") by choosing which runs to pass -- pooling across budget
    tiers, not just within one, keeps the denominator comparable when
    convergence curves are plotted against each other across tiers.

    Pooling every run for a real benchmark/budget grid means hundreds of
    thousands of points (verified against this project's own R=30,
    4-budget-tier grid: 231,000 points per benchmark) -- the generic,
    dimension-agnostic p3net.problem.objectives.pareto_front is O(n^2),
    which is minutes-to-hours at that scale. Since this project's
    objectives are always 2-dimensional (f1, f2), pool through an O(n log
    n) 2D skyline filter instead (same "specialise the common 2D case"
    approach as p3net.metrics.hypervolume's own fast path); falls back to
    the generic algorithm for any other dimensionality."""
    all_points = [obj for run in runs for obj in run.objectives]
    if not all_points:
        return []
    if len(all_points[0]) == 2:
        return _nondominated_front_2d(all_points)
    return pareto_front(all_points, lambda p: p)


def _nondominated_front_2d(points: Sequence[Objectives]) -> list[Objectives]:
    """O(n log n) nondominated-front filter for 2-objective points
    (minimisation): sort by (f1, f2) ascending, then keep a point iff its
    f2 is strictly less than the best f2 seen so far among equal-or-lower
    f1 -- the standard 2D skyline sweep. Collapses exact duplicate points
    to one (unlike the generic pareto_front, which keeps every copy since
    neither dominates the other under strict inequality) -- immaterial
    for this module's actual use (feeding hypervolume(), where a
    duplicate contributes zero additional volume), noted here so it's not
    a silent surprise if this function is ever used for something that
    cares about exact multiplicity."""
    ordered = sorted(points, key=lambda p: (p[0], p[1]))
    front: list[Objectives] = []
    best_f2 = float("inf")
    for p in ordered:
        if p[1] < best_f2:
            front.append(p)
            best_f2 = p[1]
    return front


def nadir_reference_point(points: Sequence[Objectives], *, slack: float = 1e-6) -> Objectives:
    """A hypervolume reference point: the coordinate-wise maximum (nadir)
    over `points`, nudged by `slack` so every point is STRICTLY better
    than the reference in every objective (p3net.metrics.hypervolume
    requires weakly-worse, but a point exactly on the reference
    contributes zero volume, so a small positive slack keeps every real
    point contributing something)."""
    if not points:
        raise ValueError("nadir_reference_point needs at least one point")
    dims = len(points[0])
    if any(len(p) != dims for p in points):
        raise ValueError("all points must share the same number of objectives")
    return tuple(max(p[j] for p in points) + slack for j in range(dims))
