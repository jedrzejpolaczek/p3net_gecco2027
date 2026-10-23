# Faza 1 (final design) + Faza 2 — synthetic k-ary validation of the generalised eLyMPuS

Data: 2026-08-19. Implementation: `implementation/lib/src/p3net/surrogates/elympus.py` (ELyMPuS class),
`implementation/lib/src/p3net/problem/synthetic_kary.py` (k-ary trap validation problem). Tests:
`implementation/lib/tests/test_elympus.py`, `implementation/lib/tests/test_synthetic_kary.py` — 13 tests,
all passing, built TDD (two real design bugs were caught and fixed by these tests before this note was
written, see "Bugs found during TDD" below).

## Faza 1 — final design decision

**Candidate B confirmed** (ranking/comparison against current value, mirroring FIHC's own k-ary iteration),
per the plan's working recommendation. Faza 0's literature check (`notes/lympus-nas-adaptation-literature.md`)
reinforces this: Munetomo's LINC-R generalised the same "flip has no single meaning" problem for continuous
variables by keeping the *equal/not-equal discriminator* from the binary check and only changing what
"perturbation" means — exactly the shape Candidate B takes here (see module docstring for the full
argument).

**Concrete realisation, more precise than the plan's sketch**: `PartialComparison` is generalised as a
**pairwise** operation `b(g, {v_a, v_b}, phi)` — "which of these two specific values is better for
position g, given context phi" — computed by evaluating `x` with position `g` forced to `v_a` and to
`v_b` respectively and comparing. `partial_comparison(g, v, x)` (the FIHC-facing entry point) is this
pairwise operator applied to `(v, x.values[g])`. This is closer to the source paper's literal Eq. 2 (which
compares two fully-specified values 0 and 1, not "current vs candidate") than an earlier draft of this
module that tried to cache absolute per-value fitness directly — that draft had a real, TDD-caught bug (see
below): absolute fitness is NOT reusable across two genotypes that merely share `phi`, because coordinates
outside `phi` (and outside `{g}`) can still differ between them and contribute an uncancelled additive
offset. Only the **comparison** is invariant across genotypes sharing `phi`, which is Theorem 1's actual
statement, not "same fitness" — this generalises without modification, because Theorem 1's proof only ever
uses an equal/not-equal test, never binary-specific values.

## Bugs found during TDD (documented per this project's honesty norms)

1. **Absolute-fitness caching was unsound.** First implementation cached `fitness(x, g:=v)` keyed by
   `(g, context, v)` and derived comparisons by subtracting two such cache reads. Check 1's own test
   caught a real mismatch after ~105 random samples (`Comparison.TIE` returned where ground truth was
   `Comparison.BETTER`) — root cause: two different genotypes shared the same context for `g` but differed
   in a coordinate outside `g`'s dependencies, and the cached absolute fitness from one contaminated the
   comparison computed against a fresh evaluation from the other. Fixed by caching the **pairwise
   comparison result** itself (with a `_flip` for the reverse pair), not absolute fitness.
2. **Redundant re-evaluation of the unchanged "current" value.** The FIHC-shaped access pattern
   (`rank_values` / `partial_comparison`, one call per alternative in a domain, all against the same current
   value) recomputed the current value's fitness on every call before the pairwise cache had anything to
   reuse. Fixed with a second, unconditionally-sound memoisation layer (`_fitness_cache`, keyed by the
   `Genotype` value itself — exact, not approximate, since `Genotype` is frozen/hashable) underneath
   `_evaluate`. This is a genuine two-level caching scheme, not a single flat cache.

Neither bug is cosmetic — both would have silently produced wrong linkage decisions (bug 1) or overstated
evaluation counts, understating real savings (bug 2), if shipped without the tests in
`test_elympus.py::test_partial_comparison_matches_ground_truth_when_dependencies_are_complete` and
`test_partial_comparison_reuses_cache_across_different_genotypes_sharing_context` catching them first.

## Synthetic problem

`k_ary_trap_fitness` (`synthetic_kary.py`): n_blocks independent blocks of `block_size=4` variables each,
alphabet `{0, ..., K-1}`. Per block, unitation u = count of variables equal to the "target" value 0;
block score = `B-1-u` for `u < B`, `B` for `u = B` — a direct k-ary generalisation of the source paper's
`bim_ell` (Eq. 1): deceptive optimum at u=B-1 (score 0, the worst score, one step short of B), true global
optimum only at u=B. True dependency graph: fully connected within each block, empty across blocks
(`true_dependency_graph`).

## Check 1 — correctness when eG = G

**PASS.** With `dependencies` initialised to the true graph (`eG = G`, Theorem 1's precondition),
`partial_comparison` was checked against direct ground-truth evaluation across **2000 random
(genotype, g, alternative-value) triples**, alphabet size K=5, n_blocks=5 (n=20): **0 mismatches**.

## Check 2 — guaranteed missing-linkage discovery

**PASS on correctness, PARTIAL on the complexity bound.** Starting from `dependencies` completely empty
(the harder, more realistic black-box starting point — not just one missing edge), 16 independent
mismatching `(x1, x2, g, value)` situations were sampled and passed to `discover_missing_dependency`
(n_blocks=4, block_size=4, alphabet K=4, n=16):

- **Soundness: 16/16 (100%)** discovered indices were genuine members of the true dependency block —
  `discover_missing_dependency` never invented a false dependency in this sample.
- **Termination:** every call terminated (no infinite recursion, as guaranteed by bisecting a strictly
  shrinking `diff` set).
- **Cost vs. the source paper's bound:** mean **9.0** real evaluations per discovery, max **10** —
  slightly *above* the paper's binary bound of `2*ceil(log2(n)) = 8` for n=16. This is an honest,
  documented deviation, not silently absorbed: the plan explicitly anticipated the complexity bound might
  not survive generalisation unchanged (Faza 2 instructions) — it does not, by a small margin. The most
  likely cause: with `dependencies` starting empty, the `diff` set bisected by `RecursiveLL` can be as
  large as `n-2` (everything except `g` and the one already-known coordinate), whereas the paper's
  examples typically bisect a smaller residual set already narrowed by prior partial knowledge. This
  module does not currently attempt to tighten that bound further (e.g. by seeding `diff` more precisely)
  — flagged here as a known, unresolved gap rather than fixed by adjusting the test problem to hide it.

## Check 3 — FFE savings vs. full evaluation

**PASS, modest.** First-improvement hill-climb (identical iteration order/policy to
`p3net.search_engines.p3.canonical_pyramid.first_improvement_hill_climber`) run for R=30 independent
random starts, comparing total real evaluations against an equivalent naive climber that always evaluates
directly, reusing one `ELyMPuS` instance's cache across all 30 runs (Table-4-style repeated-use scenario):

| n_blocks | n  | naive evaluations | eLyMPuS evaluations | savings |
|---|---|---|---|---|
| 3  | 12 | 940  | 816  | 13.2% |
| 6  | 24 | 1850 | 1641 | 11.3% |
| 10 | 40 | 3059 | 2705 | 11.6% |

Savings are real and consistent across scales (11-13%), but substantially smaller than the source paper's
own reported eLyMPuS savings on binary benchmarks (Table 4, commonly 30-60%+ depending on problem). This
is an honest, expected consequence of the pairwise-comparison-only caching design (Check 1's bugfix):
because absolute per-value fitness cannot be safely cached across genotypes (only pairwise comparisons
can), the k-ary generalisation reuses less per evaluation than a hypothetical unsound design would have —
the savings measured here are the real, sound number, not an inflated one.

A single cold-cache run (no prior cache to reuse) shows `elympus_count <= naive_count` always (never
worse) but no meaningful savings by itself — savings accumulate only across repeated FIHC-style access to
the same `ELyMPuS` instance, exactly as intended for its use inside a P3 pyramid's repeated `climb` calls
(Faza 3).

## Go/no-go decision

**GO — proceed to Faza 3**, with the following caveats carried forward explicitly, not glossed over:

1. The complexity bound for missing-dependency discovery is **not** proven to survive the k-ary
   generalisation unchanged — empirically close (9.0 vs. 8 mean/bound at n=16) but measurably higher.
2. Evaluation savings are real but modest (11-13%) at this scale, smaller than the source paper's own
   binary results — attributable to the stricter, TDD-corrected caching scheme this module uses (pairwise
   comparisons only, never absolute fitness, across genotypes).
3. Validation covers only the additive-separable, block-local dependency structure of `k_ary_trap_fitness`
   (mirroring the source paper's own choice of `bim_ell`) — NAS-Bench-201's true dependency structure
   between the 6 edge-operation variables is unknown and may not be block-separable at all. Faza 3/4's own
   NAS-facing smoke test is the first check of whether this generalisation transfers past a synthetic,
   separable problem.
4. Per the plan (Faza 5), only symmetric dependencies are discovered (no C4-C6 directional relations), and
   only pairwise "better/worse/tie against current" is exposed, not a full k-value ranking or ordering
   consistency check across triples of values.
