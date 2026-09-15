"""FIHC-eLyMPuS (Faza 3, notes/plans/experiments-przewozniczek-plan.md):
First-Improvement Hill Climber (same Algorithm 4 shape as
`canonical_pyramid.first_improvement_hill_climber`) driven by the k-ary
generalised eLyMPuS surrogate (`p3net.surrogates.elympus.ELyMPuS`) instead
of directly calling `elympus.fitness_fn` for every trial move -- a call to
`elympus.fitness_fn` only happens where `ELyMPuS.partial_comparison` needs
one (context cache miss / non-monotonicity spot check), not once per
alternative value tried. Whether that `fitness_fn` is itself a real
substrate evaluation or a surrogate's `.predict` is entirely up to the
`ELyMPuS` instance the caller constructs -- this module has no opinion and
does not itself distinguish the two; see the note below on this
integration's actual, non-real wiring.

This is P3-eLyMPuS (source paper's Table 5: second-best of six compared
optimisers, after the authors' own OLyMPuS, before P3-FIHCwLL), NOT full
OLyMPuS -- no PXrLL, no ILS-like perturbation, no circuit-based missing-
linkage detection (Faza 5, explicitly out of scope for this project).

Single-objective by construction (`objective_index`), matching the source
paper's own scope exactly -- P3-eLyMPuS as built here does not generalise
eLyMPuS to multi-objective; it drives ONE objective through `elympus`
while `canonical_pyramid.climb`'s surrounding pyramid machinery (GOM
sweeps, promotion) is driven by whatever `fitness_fn` the CALLER passes to
`climb` -- in the abstract, this can be real, multi-objective Pareto
dominance exactly as for the plain-FIHC canonical pyramid, and `climb`'s
own docstring describes it that way. **In this project's one production
caller** (`PrzewozniczekP3ELyMPuS`), however, `climb`'s `fitness_fn` is
`surrogate.predict`, NOT real fitness -- GOM/promotion are surrogate-
driven there too, for the harness-structural reason that reconstruction's
own module docstring explains (no direct real-substrate access from
inside `propose()`/`update()`). Do not assume this module's own
description above of "GOM/promotion on real Pareto dominance" holds for
that integration; it is a property of `climb`'s general contract, not a
guarantee about how any specific caller uses it.

**Confound warning for anyone comparing this hill climber against the
default one.** Substituting `fihc_elympus` for `climb`'s built-in
`_first_improvement_hill_climb` changes TWO things simultaneously, not
one:

1. the comparison mechanism (eLyMPuS's k-ary, linkage-discovering partial
   comparisons vs. plain first-improvement on predicted values), and
2. the objective handling -- this module is single-objective by
   construction (above), while the default climber's `_improves` accepts
   any candidate the current one does not strictly Pareto-dominate, i.e.
   it is permissively multi-objective.

An arm that swaps in this hill climber and beats one that does not
therefore does NOT isolate (1); a greedy scalar climb could outperform a
permissive multi-objective one on a scalarised metric for reasons that
have nothing to do with linkage discovery. Isolating (1) needs a third
arm: the default pyramid and gate, driven by a plain first-improvement
climb over the SAME single scalar objective this module uses. That arm
does not exist in this project yet.
"""

from __future__ import annotations

import random
from collections.abc import Callable

from p3net.problem.decoding import Validity, is_valid
from p3net.problem.genotype import Genotype, SearchSpace
from p3net.problem.objectives import Objectives
from p3net.surrogates.elympus import Comparison, ELyMPuS

_COMPARISON_SIGN = {Comparison.BETTER: 1.0, Comparison.TIE: 0.0, Comparison.WORSE: -1.0}


def fihc_elympus(
    genotype: Genotype,
    search_space: SearchSpace,
    elympus: ELyMPuS,
    rng: random.Random,
    *,
    validity: Validity | None = None,
    on_decision: Callable[[Genotype, Genotype, float, bool], None] | None = None,
) -> Genotype:
    """Same first-improvement policy, coordinate order, and alternative-
    value order as `first_improvement_hill_climber` -- the only difference
    is that acceptance is decided by `elympus.partial_comparison` (real
    evaluations happen lazily, inside `elympus`, only on a cache miss)
    instead of by evaluating `fitness_fn` directly on every trial.
    Acceptance is BETTER-or-TIE, matching `first_improvement_hill_climber`
    /`canonical_pyramid._improves`'s own "not worse" semantics (`not
    dominates(current, candidate)`, true for an exact tie) -- an earlier
    version of this function accepted only strict BETTER, silently
    skipping an alternative that ties the current value and could
    therefore land the climb at a different, non-equivalent local point
    than an otherwise-identical FIHC run would reach.

    `on_decision(current, candidate, predicted, accepted)`, if given, is
    told about every comparison, with `predicted` = +1 (BETTER), 0 (TIE) or
    -1 (WORSE); it has no effect on the climb."""
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
            comparison = elympus.partial_comparison(i, value, current)
            if on_decision is not None:
                on_decision(
                    current,
                    candidate,
                    _COMPARISON_SIGN[comparison],
                    comparison in (Comparison.BETTER, Comparison.TIE),
                )
            if comparison in (Comparison.BETTER, Comparison.TIE):
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
