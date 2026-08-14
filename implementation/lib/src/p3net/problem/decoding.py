"""Generic decoding/validity protocols: user-pluggable D and g."""

from __future__ import annotations

from collections.abc import Callable, Iterable

from p3net.problem.genotype import Genotype

Decoder = Callable[[Genotype], object]
"""Any callable Genotype -> T, for whatever target type T a concrete problem
needs (a network description, a configuration dict, anything). The
library's search engines and surrogates never depend on T's shape."""

Validity = Callable[[Genotype], float]
"""A callable Genotype -> float returning a structural feasibility score.
A genotype is valid iff the score is <= 0 (the common boolean case maps to
{-1, +1}); real-valued so a graded infeasibility measure can be used if a
concrete problem defines one."""


def is_valid(genotype: Genotype, validity: Validity) -> bool:
    """x is valid iff g(x) <= 0."""
    return validity(genotype) <= 0


def valid_subset(genotypes: Iterable[Genotype], validity: Validity) -> list[Genotype]:
    """Lambda* = {x in Lambda : g(x) <= 0}, generic over any SearchSpace."""
    return [g for g in genotypes if is_valid(g, validity)]
