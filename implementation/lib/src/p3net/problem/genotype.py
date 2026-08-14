"""Generic search-space representation: a Cartesian product of variable domains."""

from __future__ import annotations

import math
import random
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True)
class CategoricalDomain:
    """A finite set of allowed values for one genotype coordinate."""

    values: tuple[Any, ...]

    def __post_init__(self) -> None:
        if len(self.values) == 0:
            raise ValueError("CategoricalDomain needs at least one value")

    def sample(self, rng: random.Random) -> Any:
        return rng.choice(self.values)


def discretize_log_uniform(low: float, high: float, n: int) -> tuple[float, ...]:
    """Build an n-point log-spaced grid over [low, high]. A usable
    discretisation policy for continuous hyperparameters such as learning
    rate (Problem Formulation, option (i))."""
    if low <= 0 or high <= 0:
        raise ValueError("log-uniform discretisation requires low, high > 0")
    if n < 2:
        raise ValueError("need at least two grid points")
    log_low, log_high = math.log(low), math.log(high)
    step = (log_high - log_low) / (n - 1)
    return tuple(math.exp(log_low + i * step) for i in range(n))


def discretize_linear(low: float, high: float, n: int) -> tuple[float, ...]:
    """Build an n-point linearly spaced grid over [low, high]."""
    if n < 2:
        raise ValueError("need at least two grid points")
    step = (high - low) / (n - 1)
    return tuple(low + i * step for i in range(n))


@dataclass(frozen=True)
class Genotype:
    """One point in a SearchSpace: an assignment of one value per domain."""

    values: tuple[Any, ...]

    def __len__(self) -> int:
        return len(self.values)

    def with_values(self, *, indices: Sequence[int], new_values: Sequence[Any]) -> Genotype:
        """Return a copy with the coordinates at `indices` replaced by
        `new_values`, all other coordinates unchanged. Used by optimal
        mixing to build a proposal restricted to a linkage subset F."""
        updated = list(self.values)
        for i, v in zip(indices, new_values):
            updated[i] = v
        return Genotype(values=tuple(updated))


@dataclass(frozen=True)
class SearchSpace:
    """A Cartesian product of variable domains: Lambda = Lambda_1 x ... x Lambda_n.

    Domain-agnostic by design: this class knows nothing about "architecture
    edges" or "hyperparameters" -- a concrete problem (e.g.
    ../experiments/search_spaces/nas_genotype.py) builds one of these out of
    whatever domains it needs, including continuous coordinates already
    discretised via discretize_log_uniform/discretize_linear or a
    caller-supplied discretisation.
    """

    domains: tuple[CategoricalDomain, ...]

    @property
    def n(self) -> int:
        return len(self.domains)

    def sample_uniform(self, rng: random.Random) -> Genotype:
        return Genotype(values=tuple(d.sample(rng) for d in self.domains))

    def contains(self, genotype: Genotype) -> bool:
        if len(genotype.values) != self.n:
            return False
        return all(v in d.values for v, d in zip(genotype.values, self.domains))
