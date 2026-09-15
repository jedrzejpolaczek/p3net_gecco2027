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

import random
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
    #: No default, matching this codebase's convention that every
    #: stateful, randomised component is threaded a caller-supplied,
    #: explicitly seeded RNG -- see e.g. p3net.methods.p3net.P3Net,
    #: BartnikP3, PrzewozniczekP3ELyMPuS. Only consulted when
    #: `verify_probability > 0.0`, but required regardless so a caller
    #: cannot silently end up with an unseeded, wall-clock-seeded instance
    #: by omission.
    rng: random.Random
    dependencies: dict[int, set[int]] = field(default_factory=dict)
    #: Probability of spot-checking a cache hit from a genotype other than
    #: the one that established it (see `_pairwise_comparison`'s
    #: docstring). Defaults to 0.0 -- off -- so a caller that already
    #: knows/seeds the true dependency graph (Check 1's `eG = G`
    #: precondition, as every existing test in test_elympus.py does) pays
    #: exactly zero extra evaluations, matching this module's own
    #: documented zero-overhead guarantee for that case. A caller that
    #: does NOT seed the true graph (the actual production case in
    #: `PrzewozniczekP3ELyMPuS`, which starts `dependencies` empty) MUST
    #: set this above 0.0, or `dependencies` never grows at all --
    #: `discover_missing_dependency` exists and is independently tested
    #: (Check 2) but nothing ever calls it otherwise.
    verify_probability: float = 0.0
    evaluation_count: int = field(default=0, init=False)
    _table: dict[int, dict[Context, dict[Any, Comparison]]] = field(
        default_factory=dict, init=False, repr=False
    )
    #: One witness genotype per (g, context, value_a, value_b) cache entry
    #: -- mirrors `_table`'s own shape exactly -- recording whose
    #: evaluation actually produced that entry. Used by
    #: `_pairwise_comparison` to run Theorem 1's own non-monotonicity spot
    #: check on a cache hit from a genuinely different genotype; without
    #: this, `dependencies` never grows past whatever the caller seeds it
    #: with, since nothing would ever call `discover_missing_dependency`
    #: (see that method's docstring and
    #: notes/lympus-nas-adaptation-validation.md). MUST be tracked per
    #: entry, not per (g, context) alone: several distinct value pairs
    #: under one context can each be first computed by a different
    #: genotype, and a coarser per-context witness would not necessarily
    #: correspond to whichever genotype produced the specific entry being
    #: spot-checked -- an earlier version of this field did exactly that
    #: and could inject false dependencies as a result.
    _context_witness: dict[int, dict[Context, dict[Any, Genotype]]] = field(
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
        micro-optimisation detail.

        Every call reaching this method comes from `partial_comparison`
        (directly, or via this method's own same-arguments recursive
        retry below), whose contract guarantees `value_b ==
        genotype.values[g]` -- asserted, not just assumed, since a future
        caller violating it would otherwise silently corrupt
        `discover_missing_dependency`'s precondition rather than fail
        loudly. Both cache orientations, (value_a, value_b) and its flip,
        are therefore always written TOGETHER from a single fresh
        computation below -- there is no code path that ever writes only
        one direction, so a lookup can never find one orientation cached
        without the other already being cached too (proof by induction
        from the empty table; the earlier reverse-lookup shortcut this
        method used to have was therefore always dead code and has been
        removed).

        A cache HIT from a genotype other than the one whose evaluation
        actually produced THIS EXACT (g, context, value_a, value_b) entry
        -- `_context_witness` is keyed by the full pair, not by `value_b`
        alone -- is spot-checked against a fresh, direct recomputation for
        THIS genotype (Theorem 1's own non-monotonicity check): if they
        disagree, `dependencies[g]` is provably still missing a real
        dependency (some coordinate differing between the two genotypes,
        outside the currently-known context, actually affects g's local
        behaviour) -- `discover_missing_dependency` is invoked to find and
        record it, `g`'s now-stale cache is cleared, and the freshly
        computed, correct verdict is used instead of the stale one. This
        is what lets `dependencies` grow from an initially-empty (or
        partial) graph at runtime rather than requiring the caller to seed
        the true graph up front.

        Keying witnesses by the pair, not by `value_b` alone, is
        deliberate and load-bearing, not an arbitrary choice: a `value_b`
        -only key gets overwritten by ANY call sharing that value, even
        one for a completely different `value_a` -- so a later spot check
        for (value_a=X, value_b) could end up comparing against a witness
        whose own evaluation only ever confirmed (value_a=Y, value_b),
        never X. That witness's `values` can legitimately agree with
        `cached` by coincidence or by an earlier successful spot check for
        a DIFFERENT value_a, while `cached` itself was established by some
        earlier, different genotype entirely -- so the mismatch check
        compares the wrong pairing and `discover_missing_dependency` can
        report a real-looking but false dependency. This is not a
        hypothetical: it is exactly what a `value_b`-keyed witness design
        produced in practice (reproducible with search_engines'
        `k_ary_trap_fitness` on a 2-block problem, rng seed 3) before this
        docstring paragraph was written. The cost of keying per pair
        instead is that only the (value_a, value_b) orientation actually
        queried first ever accumulates a witness -- the flip orientation
        stays permanently un-spot-checked until it happens to be queried
        directly itself -- a real, accepted reduction in discovery
        coverage, preferred here over a coverage-improving change that
        reintroduces false positives."""
        if value_a == value_b:
            return Comparison.TIE
        if value_b != genotype.values[g]:
            # A real `raise`, not `assert`: assertions are stripped under
            # `-O`/`PYTHONOPTIMIZE`, which would silently turn this
            # documented "fail loudly" contract into exactly the silent
            # precondition corruption it exists to prevent.
            raise ValueError(
                "_pairwise_comparison's caller contract requires value_b == "
                "genotype.values[g] (only partial_comparison calls this method); "
                "discover_missing_dependency's precondition depends on it"
            )
        ctx = self.context_of(g, genotype)
        ctx_table = self._table.setdefault(g, {}).setdefault(ctx, {})
        ctx_witnesses = self._context_witness.setdefault(g, {}).setdefault(ctx, {})
        key = (value_a, value_b)
        witness = ctx_witnesses.get(key)
        cached = ctx_table.get(key)
        if cached is not None:
            if (
                witness is not None
                and witness.values != genotype.values
                and self.verify_probability > 0.0
                and self.rng.random() < self.verify_probability
            ):
                fresh = Comparison.of(
                    self._evaluate(genotype.with_values(indices=[g], new_values=[value_a])),
                    self._evaluate(genotype),
                )
                if fresh != cached:
                    found = self.discover_missing_dependency(g, value_a, witness, genotype)
                    if found is not None:
                        self._table[g] = {}
                        self._context_witness[g] = {}
                        return self._pairwise_comparison(g, value_a, value_b, genotype)
                    # Discovery could not pin down a culprit (its own
                    # defensive branch) -- still fix up this one entry so
                    # future lookups don't keep serving the now-known-wrong
                    # cached verdict indefinitely, even though the root
                    # cause (an incomplete `dependencies[g]`) is not fully
                    # resolved.
                    ctx_table[key] = fresh
                    ctx_table[(value_b, value_a)] = _flip(fresh)
                    ctx_witnesses[key] = genotype
                    return fresh
            return cached
        fitness_a = self._evaluate(genotype.with_values(indices=[g], new_values=[value_a]))
        fitness_b = self._evaluate(genotype)
        result = Comparison.of(fitness_a, fitness_b)
        ctx_table[key] = result
        ctx_table[(value_b, value_a)] = _flip(result)
        # `genotype` is a valid witness for `key` only (its own g-value ==
        # value_b, key's second element); the reverse entry's witness
        # would need a genotype whose own g-value == value_a instead, so
        # it is deliberately left unset here (see docstring above).
        ctx_witnesses[key] = genotype
        return result

    def partial_comparison(self, g: int, value: Any, genotype: Genotype) -> Comparison:
        """Directional comparison of `value` against genotype.values[g]
        within genotype's current context of g."""
        return self._pairwise_comparison(g, value, genotype.values[g], genotype)

    def rank_values(self, g: int, genotype: Genotype) -> list[Any]:
        """The k-1 comparisons against the current value, best alternative
        first (BETTER before TIE before WORSE). NOT currently called by
        `p3net.search_engines.p3.fihc_elympus.fihc_elympus`, which instead
        does exactly the random-order, first-improvement iteration this
        method's ranking could replace -- kept as a public, independently
        useful k-ary generalisation of "which alternative is best" (and
        exercised by its own tests), not because anything in this project
        currently consumes it."""
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
