"""Telescoping construction: reconstructing an absolute f1 estimate along a
sweep chain."""

from __future__ import annotations

from dataclasses import dataclass

from p3net.harness.runner import Observation
from p3net.problem.genotype import Genotype
from p3net.surrogates.relative_linkage_aware import RelativeLinkageAwareSurrogate


class AncestorNotEvaluatedError(ValueError):
    """Raised when the telescoping construction would bottom out on a
    genotype without a known, fully evaluated f1 -- must never happen."""


@dataclass(frozen=True)
class ChainStep:
    x_prev: Genotype
    x_next: Genotype
    subset: frozenset[int]


def telescoped_estimate(
    ancestor: Observation,
    chain: list[ChainStep],
    surrogate: RelativeLinkageAwareSurrogate,
    known_evaluated: set[Genotype],
    *,
    objective_index: int = 0,
) -> float:
    """f_hat_1(x_m) = f1(x_0) - sum_i delta_hat_{F_i}(x_{i-1}, x_i),
    telescoping back along the chain of tentatively accepted modifications
    to the nearest fully-evaluated ancestor x_0. Reduces to the single-step
    case f_hat_1(x') = f1(x) - delta_hat_F(x, x') when len(chain) == 1.

    `ancestor` must be drawn from H_t (checked via `known_evaluated`) --
    this function refuses to run rather than silently bottoming out on an
    unknown value.
    """
    if ancestor.genotype not in known_evaluated:
        raise AncestorNotEvaluatedError(
            "telescoping ancestor x_0 must be drawn from H_t (a fully "
            "evaluated genotype); got one with no known f1"
        )
    estimate = ancestor.objectives[objective_index]
    for step in chain:
        delta = surrogate.predict(step.x_prev, step.x_next, step.subset)
        estimate -= delta
    return estimate
