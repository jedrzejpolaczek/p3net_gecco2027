"""Seed policy: R (independent search runs) vs s (evaluation-noise repeats)."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SeedPolicy:
    """R independent search-run seeds, kept strictly distinct from s
    (repeats of a single stochastic query, see
    p3net.problem.objectives.evaluate_with_noise). The two concepts must
    never collapse into a single "seed" parameter."""

    run_seeds: tuple[int, ...]
    s: int = 1

    def __post_init__(self) -> None:
        if len(self.run_seeds) == 0:
            raise ValueError("need at least one run seed")
        if self.s < 1:
            raise ValueError("s must be >= 1")
        if len(set(self.run_seeds)) != len(self.run_seeds):
            raise ValueError("run seeds must be unique")

    @property
    def r(self) -> int:
        return len(self.run_seeds)
