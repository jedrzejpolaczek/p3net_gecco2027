"""eLyMPuS (empirical Limited Monotonical Perfect Surrogate), generalised
from `przewozniczek2026lympus`'s strictly binary/pseudo-Boolean definition
to k-ary categorical domains (k > 2).

**This generalisation is this project's own design, not something
Przewoźniczek et al. published.** The source paper defines eLyMPuS's core
mechanism -- partial comparisons b(x_g, phi, x) in Eq. 2, and the
non-monotonicity check's clauses C1-C6 -- exclusively over binary flips
(x_g -> NOT x_g). NAS-Bench-201's genotype has 6 categorical variables with
5 possible values each, where "flip" has no single well-defined meaning (4
possible target values, not 1). The paper's own Conclusions (p.652) name
this generalisation as unfinished future work: "the proposed mechanisms are
not limited to the binary search space and apply to integer-based solution
encoding... which is a future work step." See
notes/lympus-nas-adaptation-literature.md (Faza 0) for the literature check
confirming no prior publication fills this gap, and
notes/lympus-nas-adaptation-validation.md (Faza 2) for the synthetic
validation results this module's correctness claims rest on.

Design choice made here ("Candidate B" in
notes/plans/experiments-przewozniczek-plan.md, Faza 1): generalise the
binary comparison b(x_g, phi, x) in {{0},{1},{0,1}} to a per-alternative-
value comparison against the CURRENT value of x_g, evaluated one alternative
at a time -- k-1 comparisons per variable, mirroring the source paper's own
FIHC (Algorithm 4), which already iterates "for all values v in the domain
of x_i" k-arily. Two independent pieces of supporting evidence found in
Faza 0 justify this specific choice over "Kandydat A" (a directed,
per-value-transition scheme with O(k^2) pairs to track):
1. FIHC's existing k-ary iteration already implies "compare current value
   against every alternative", not "compare every pair of values" -- so
   Candidate B requires no new concept FIHC didn't already have.
2. Munetomo's LINC-R (linkage identification for real-coded GAs) solved the
   structurally analogous problem -- "flip has no single meaning" -- for
   continuous variables by replacing the flip with a perturbation and
   keeping the SAME equal/not-equal discriminator used by the binary
   non-linearity check. That discriminator (see `discover_missing_
   dependency` below) never actually depends on the alphabet being binary
   -- Theorem 1/2's proofs in the source paper only use an equivalence
   test, not the specific values {0,1} -- so this module's bisection logic
   is a faithful generalisation of Pseudocode 3, not a new algorithm.

Known, explicitly out-of-scope limitations (Faza 5 of the plan): symmetric
dependencies only (no C4-C6 directional discovery); no full k-value ranking
beyond "better/worse/tie against the current value" (a full order over all
k values was considered and rejected as unneeded for FIHC's use case, which
only ever needs "is this alternative at least as good as what's there
now").
"""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any

from p3net.problem.genotype import Genotype, SearchSpace


class Comparison(Enum):
    BETTER = auto()
    WORSE = auto()
    TIE = auto()

    @staticmethod
    def of(candidate_fitness: float, current_fitness: float) -> "Comparison":
        if candidate_fitness < current_fitness:
            return Comparison.BETTER
        if candidate_fitness > current_fitness:
            return Comparison.WORSE
        return Comparison.TIE


Context = tuple[tuple[int, Any], ...]

_RANK_ORDER = {Comparison.BETTER: 0, Comparison.TIE: 1, Comparison.WORSE: 2}
_FLIP = {Comparison.BETTER: Comparison.WORSE, Comparison.WORSE: Comparison.BETTER, Comparison.TIE: Comparison.TIE}


def _flip(c: Comparison) -> Comparison:
    return _FLIP[c]


@dataclass
class ELyMPuS:
    """One instance tracks the empirical VIG and cached partial comparisons
    for one search space + one (real, expensive) fitness function. Trained
    on the fly, exactly like the source paper -- there is no separate
    "build" phase, `partial_comparison` computes and caches lazily."""

    search_space: SearchSpace
    fitness_fn: Callable[[Genotype], float]
    dependencies: dict[int, set[int]] = field(default_factory=dict)
    evaluation_count: int = field(default=0, init=False)
    _table: dict[int, dict[Context, dict[Any, Comparison]]] = field(
        default_factory=dict, init=False, repr=False
    )
    #: Plain memoisation of the real fitness function itself (Genotype is
    #: frozen/hashable, so this is exact, not approximate) -- independent
    #: of the context-scoped comparison cache above. Needed because
    #: `rank_values` compares the SAME current genotype against every
    #: alternative value in its domain; without this, "the current value's
    #: fitness" would be recomputed once per alternative compared, wasting
    #: real evaluations on a value that never changes within one call.
    _fitness_cache: dict[Genotype, float] = field(default_factory=dict, init=False, repr=False)

    def __post_init__(self) -> None:
        for g in range(self.search_space.n):
            self.dependencies.setdefault(g, set())

    def context_of(self, g: int, genotype: Genotype) -> Context:
        """phi: the hyperplane fixing every currently-known dependency of g
        to its value in `genotype`. Two genotypes that agree on
        context_of(g, .) are, by construction, assumed indistinguishable
        for g's local behaviour -- this is the caching key that gives
        eLyMPuS its evaluation savings, and the assumption Theorem 1
        guarantees correct only once `dependencies[g]` equals the true
        variable interaction graph's neighbourhood of g."""
        deps = sorted(self.dependencies[g])
        return tuple((i, genotype.values[i]) for i in deps)

    def _evaluate(self, genotype: Genotype) -> float:
        """Plain memoised fitness lookup (`_fitness_cache`), on top of
        which the context-scoped comparison cache above is built. A cache
        hit here means the exact same genotype (by value, Genotype is
        frozen/hashable) was evaluated before -- always sound, no
        dependency-completeness assumption involved, unlike `_table`."""
        cached = self._fitness_cache.get(genotype)
        if cached is not None:
            return cached
        self.evaluation_count += 1
        result = self.fitness_fn(genotype)
        self._fitness_cache[genotype] = result
        return result

    def _compute(self, g: int, value: Any, genotype: Genotype) -> Comparison:
        current_fitness = self._evaluate(genotype)
        candidate = genotype.with_values(indices=[g], new_values=[value])
        candidate_fitness = self._evaluate(candidate)
        return Comparison.of(candidate_fitness, current_fitness)

    def _pairwise_comparison(
        self, g: int, value_a: Any, value_b: Any, genotype: Genotype
    ) -> Comparison:
        """b(g, {value_a, value_b}, phi) as defined by Eq. 2: which of the
        two fully-specified values is better for position g, given phi =
        context_of(g, genotype). Cached and reused by (g, context,
        value_a, value_b) -- NOT by caching the two values' absolute
        fitness separately. An earlier version of this method cached
        absolute fitness per (g, context, value) and subtracted two cache
        reads to get the comparison; that is unsound in general, because
        two genotypes sharing the same context can still differ OUTSIDE
        the context (in coordinates that are not dependencies of g), and
        absolute fitness picks up that irrelevant difference as an
        additive offset that does not cancel unless it is subtracted
        within a single evaluation call. Comparisons DO cancel that offset
        (Theorem 1's actual guarantee: two genotypes agreeing on phi give
        the SAME comparison outcome, not the same absolute fitness) -- a
        real bug caught by Faza 2's own correctness test (Check 1) failing
        on a genuine cross-genotype cache-reuse mismatch, not a
        micro-optimisation detail."""
        if value_a == value_b:
            return Comparison.TIE
        ctx = self.context_of(g, genotype)
        ctx_table = self._table.setdefault(g, {}).setdefault(ctx, {})
        key = (value_a, value_b)
        cached = ctx_table.get(key)
        if cached is not None:
            return cached
        reverse_cached = ctx_table.get((value_b, value_a))
        if reverse_cached is not None:
            result = _flip(reverse_cached)
            ctx_table[key] = result
            return result
        fitness_a = self._evaluate(genotype.with_values(indices=[g], new_values=[value_a]))
        fitness_b = self._evaluate(genotype.with_values(indices=[g], new_values=[value_b]))
        result = Comparison.of(fitness_a, fitness_b)
        ctx_table[key] = result
        ctx_table[(value_b, value_a)] = _flip(result)
        return result

    def partial_comparison(self, g: int, value: Any, genotype: Genotype) -> Comparison:
        """Directional comparison of `value` against genotype.values[g]
        within genotype's current context of g."""
        return self._pairwise_comparison(g, value, genotype.values[g], genotype)

    def rank_values(self, g: int, genotype: Genotype) -> list[Any]:
        """The k-1 comparisons against the current value, best alternative
        first (BETTER before TIE before WORSE) -- the direct k-ary
        generalisation FIHC-eLyMPuS (Faza 3) needs in place of iterating
        `domain.values` in random order and testing one at a time."""
        domain = self.search_space.domains[g]
        alternatives = [v for v in domain.values if v != genotype.values[g]]
        scored = [(self.partial_comparison(g, v, genotype), v) for v in alternatives]
        scored.sort(key=lambda pair: _RANK_ORDER[pair[0]])
        return [v for _, v in scored]

    def discover_missing_dependency(
        self, g: int, value: Any, x1: Genotype, x2: Genotype
    ) -> int | None:
        """RecursiveLL (source paper's Pseudocode 3), generalised. Caller's
        precondition (mirroring the paper): `x1` and `x2` agree on
        context_of(g, .) (same known-dependency context) but
        partial_comparison(g, value, x1) != partial_comparison(g, value,
        x2) computed directly (bypassing the cache -- see `_compute`) --
        i.e. some variable that differs between x1 and x2 outside the
        already-known context is a real, undiscovered dependency of g.
        Bisects that differing set exactly like RecForGroup; the only
        change bisection needs for k-ary values is that the equality test
        between two Comparison outcomes has three possible values instead
        of two -- irrelevant to the bisection logic itself, which only
        ever asks "same or different", matching Theorem 2's proof (it uses
        an equivalence test, never the size of the underlying alphabet).
        Adds the discovered index to `dependencies[g]` and returns it, or
        returns None if no variable in the differing set is actually
        responsible (defensive -- should not happen if the precondition
        holds, matching Theorem 2's guarantee)."""
        known = self.dependencies[g]
        diff = [
            i
            for i in range(self.search_space.n)
            if i != g and i not in known and x1.values[i] != x2.values[i]
        ]
        if not diff:
            return None
        found = self._bisect(g, value, x1, x2, diff)
        if found is not None:
            self.dependencies[g].add(found)
        return found

    def _bisect(
        self, g: int, value: Any, x1: Genotype, x2: Genotype, diff: list[int]
    ) -> int | None:
        if len(diff) == 1:
            return diff[0]
        mid = len(diff) // 2
        first_half = diff[:mid]
        x_mid = x1.with_values(
            indices=first_half, new_values=[x2.values[i] for i in first_half]
        )
        c1 = self._compute(g, value, x1)
        c_mid = self._compute(g, value, x_mid)
        if c1 == c_mid:
            return self._bisect(g, value, x_mid, x2, diff[mid:])
        return self._bisect(g, value, x1, x_mid, first_half)
