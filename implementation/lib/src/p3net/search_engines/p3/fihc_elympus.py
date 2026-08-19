"""FIHC-eLyMPuS (Faza 3, notes/plans/experiments-przewozniczek-plan.md):
First-Improvement Hill Climber (same Algorithm 4 shape as
`canonical_pyramid.first_improvement_hill_climber`) driven by the k-ary
generalised eLyMPuS surrogate (`p3net.surrogates.elympus.ELyMPuS`) instead
of the real fitness function for every trial move -- a real evaluation only
happens where `ELyMPuS.partial_comparison` needs one (context cache miss),
not once per alternative value tried.

This is P3-eLyMPuS (source paper's Table 5: second-best of six compared
optimisers, after the authors' own OLyMPuS, before P3-FIHCwLL), NOT full
OLyMPuS -- no PXrLL, no ILS-like perturbation, no circuit-based missing-
linkage detection (Faza 5, explicitly out of scope for this project).

Single-objective by construction (`objective_index`), matching the source
paper's own scope exactly -- P3-eLyMPuS as built here does not generalise
eLyMPuS to multi-objective; it drives ONE objective through the surrogate
while `canonical_pyramid.climb`'s surrounding pyramid machinery (GOM
sweeps, promotion) stays on real, multi-objective Pareto dominance exactly
as for the plain-FIHC canonical pyramid. See `climb`'s own docstring for
how the two compose.
"""

from __future__ import annotations

import random
from collections.abc import Callable

from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives
from p3net.surrogates.elympus import Comparison, ELyMPuS


def fihc_elympus(
    genotype: Genotype,
    search_space: SearchSpace,
    elympus: ELyMPuS,
    rng: random.Random,
    *,
    validity: Validity | None = None,
) -> Genotype:
    """Same first-improvement policy, coordinate order, and alternative-
    value order as `first_improvement_hill_climber` -- the only difference
    is that acceptance is decided by `elympus.partial_comparison` (real
    evaluations happen lazily, inside `elympus`, only on a cache miss)
    instead of by evaluating `fitness_fn` directly on every trial."""
    current = genotype
    order = list(range(search_space.n))
    rng.shuffle(order)
    for i in order:
        domain = search_space.domains[i]
        alternatives = [v for v in domain.values if v != current.values[i]]
        rng.shuffle(alternatives)
        for value in alternatives:
            candidate = current.with_values(indices=[i], new_values=[value])
            if validity is not None and not is_valid(candidate, validity):
                continue
            if elympus.partial_comparison(i, value, current) == Comparison.BETTER:
                current = candidate
                break
    return current


def make_elympus_fitness_adapter(
    fitness_fn: Callable[[Genotype], Objectives], *, objective_index: int = 0
) -> Callable[[Genotype], float]:
    """Adapts a multi-objective `fitness_fn` into the scalar callable
    `ELyMPuS` expects, selecting one objective -- the single-objective
    boundary documented at module level. Callers build one `ELyMPuS`
    instance per objective they want driven through the surrogate (in
    practice, this project only ever drives the primary objective, e.g.
    accuracy, leaving the secondary objective's real evaluation as the
    thing that decides GOM/promotion acceptance in `climb`)."""

    def scalar_fitness(genotype: Genotype) -> float:
        return fitness_fn(genotype)[objective_index]

    return scalar_fitness
