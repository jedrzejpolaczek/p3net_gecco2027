# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project does not yet follow strict [Semantic Versioning](https://semver.org/)
until a first `0.1.0` release is reached.

## [Unreleased]

This package is a fork of `implementation/experiments` (copied 2026-08-19, `vendor/` and `data/` are
directory junctions back to the original so the NATS-Bench archive and vendored deps are not duplicated on
disk; `results/` starts empty). Everything above this section is inherited history from that fork point;
everything below is specific to this package (notes/plans/experiments-przewozniczek-plan.md).

### Added (P3-eLyMPuS isolation experiment -- Fazy 0-4 of notes/plans/experiments-przewozniczek-plan.md, 2026-08-19)

Direct diagnostic test of hypotheses (i)-(ii) from `conclusions/main.tex` ("Why the results are what they
are"), the counterpart to the sibling `experiments-bartnik` package's own isolation experiment: reconstructs
and, where the source paper leaves a genuine gap, generalises Przewoźniczek et al.'s eLyMPuS/OLyMPuS
(`przewozniczek2026lympus`) -- never previously tested on NAS or on any non-binary domain -- run inside this
harness against the SAME baseline set `p3net` itself is compared against, plus `p3net` as a direct
engine-vs-engine reference point.

**Faza 0 (literature check, done before any code)**: no published generalisation of eLyMPuS's binary
partial-comparison mechanism / non-monotonicity check to k-ary categorical domains exists (WebSearch,
cross-checked against `notes/design_space_mechanisms.md` and `notes/ga_landscape_2026.md`); the source paper's
own Conclusions name this generalisation as unfinished future work. The closest methodological precedent
(Munetomo's LINC-R, generalising the structurally analogous "flip has no single meaning" problem for
continuous variables) supports Candidate B (rank/compare-against-current) over Candidate A
(directed-transition, O(k^2)). Full writeup: `notes/lympus-nas-adaptation-literature.md`.

**Faza 1-2 (design + synthetic validation, library)**: `p3net.surrogates.elympus.ELyMPuS` (Candidate B,
pairwise comparison against the current value, k-1 comparisons per variable) and
`p3net.problem.synthetic_kary.k_ary_trap_fitness` (k-ary generalisation of the source paper's `bim_ell`, known
ground-truth dependency structure). Validated on 3 checks before any NAS-facing code: (1) correctness when
`eG=G`, 0/2000 mismatches; (2) guaranteed missing-dependency discovery, 16/16 sound, but the complexity bound
does not survive the generalisation unchanged (mean 9.0 vs. the binary bound of 8 at n=16 -- an honest,
documented gap, not hidden); (3) real evaluation savings, 11-13% across scales, smaller than the source
paper's own binary results (attributed to a stricter, TDD-corrected caching scheme -- only pairwise
comparisons are cacheable across genotypes, not absolute fitness, a real bug caught and fixed during TDD, see
`notes/lympus-nas-adaptation-validation.md`). Go decision, with all three caveats carried forward explicitly.
13 new tests, `lib/tests/test_elympus.py` + `lib/tests/test_synthetic_kary.py`.

**Faza 3 (library)**: `p3net.search_engines.p3.fihc_elympus` -- First-Improvement Hill Climber (same Algorithm
4 shape as `canonical_pyramid.first_improvement_hill_climber`) driven by `ELyMPuS.partial_comparison` instead
of direct fitness calls; composes with `canonical_pyramid.climb` via its existing `hill_climber` parameter
(GOM sweeps and promotion checks unchanged, still driven by `climb`'s own `fitness_fn`). P3-eLyMPuS only
(source paper's Table 5: second-best of six compared optimisers) -- not full OLyMPuS (plan's Faza 5: no
PXrLL, no ILS-like perturbation, no circuit-based missing-linkage detection).

**Faza 4**: `methods/przewozniczek_p3elympus.py::PrzewozniczekP3ELyMPuS` -- structurally mirrors the sibling
`experiments-bartnik` package's `BartnikP3` (same `CanonicalPyramid`, same lambda-quantile acceptance gate,
same ell-random warm-up), swapping the local-search step for FIHC-eLyMPuS. Documented architectural
consequence, stated plainly in the module's own docstring: this harness's `Method` protocol gives no method
direct substrate access, so -- exactly like `BartnikP3` -- both `climb`'s GOM/promotion loop and `ELyMPuS`'s
own internal fitness calls are driven by an `AbsoluteRandomForestSurrogate` fit on real history, not the real
substrate. This means the FFE savings Faza 2 measured for eLyMPuS translate, within this integration, into
savings on *surrogate-predict* calls during a climb, not real NATS-Bench queries -- those only ever happen
once per `propose()` call, on the single gated final candidate. Flagged explicitly rather than letting the
source paper's "cheap comparisons instead of expensive evaluations" framing imply something this integration
doesn't deliver. `configs/methods/przewozniczek_p3elympus.yaml` (`default_grid: false`); wired into
`scripts/run_experiment.py::build_method`'s if-chain and its `parametrize`d wiring test
(`tests/test_run_experiment.py`); new `scripts/run_przewozniczek_isolation.py`, mirroring
`run_bartnik_isolation.py`'s smoke test -> full grid -> Wilcoxon+Holm+Cliff's-delta pipeline, scoped to
`przewozniczek_p3elympus` vs. the nine-method baseline set above, R=30 seeds x {100, 350} budgets on
`nas_bench_201`. 9 new tests, `tests/test_przewozniczek_p3elympus.py`.

**Verification**: `uv run pytest` green in both `implementation/lib` (155 passed) and
`implementation/experiments-przewozniczek` (239 passed, 2 skipped -- the usual opt-in-only live-JAHS-Bench-201
skips, unrelated to this change) after this change.

**Not run by this change (manual, per this project's own established convention)**: the full grid --
`uv run python scripts/run_przewozniczek_isolation.py` from `implementation/experiments-przewozniczek` -- R=30
seeds x {100, 350} budgets x 10 methods = 600 real NATS-Bench queries.

### Added (architecture-only NAS-Bench-201 isolation experiment -- Fazy 0-3 of glimmering-swimming-book.md, 2026-08-18)

Built to directly test one hypothesis raised in `conclusions/main.tex` ("Why the results are what they
are"): does this project's own joint architecture+hyperparameter genotype extension explain why P3Net fails
to separate from `random_search` anywhere, given that the closest prior work, Bartnik
(`bartnik2026evolutionary`), showed a similar surrogate-assisted linkage-learning algorithm winning on
architecture-only NAS-Bench-201. New code, verified but **not yet run against real data** -- that step is
manual (below).

**Faza 0 (dependency verification)**: `nats-bench` (PyPI) confirmed real and installable; its
`get_more_info(index, dataset, hp="200")` returns `test-accuracy` for `dataset="cifar10"`, and
`get_cost_info(index, dataset, hp="200")` returns `flops` (deterministic, architecture-only) -- verified by
installing the package in isolation and reading its actual source, not from documentation alone. Confirmed
NAS-Bench-201/`nats_bench` does **not** expose GPU energy consumption (Bartnik's own $f_2$) as a queryable
field -- she measured it herself, on her own hardware (`related_work/main.tex`). $f_2$ for this experiment is
therefore **FLOPs**, a documented deviation, not a silent substitution. Dataset defaults to `cifar10`,
flagged as an assumption (Bartnik's own choice isn't precisely documented in this project's related work).
Added `nats-bench>=1.8` to `pyproject.toml` (also restored an undeclared `matplotlib` dependency,
`reporting/plots.py` needs it and it silently disappeared on `uv sync` once `pyproject.toml` was touched --
unrelated to this feature, fixed in passing since it broke the whole suite otherwise). New `refs.bib` entry
`dong2021natsbench` (Dong, Liu, Musial, Gabrys, IEEE TPAMI 2021), verified via WebSearch.

**Faza 1**: `search_spaces/nas_bench_201_genotype.py` -- architecture-only mirror of `nas_genotype.py` minus
the Θ domains (6 edges, no hyperparameters). `genotype_to_arch_str` verified directly against
`nats_bench.genotype_utils.TopologyStructure.tostr()`'s own source. 11 new tests,
`tests/test_nas_bench_201_genotype.py`.

**Faza 2**: `substrates/nas_bench_201.py` -- `NASBench201Substrate`, mirroring `nas_hpo_bench_ii.py`'s
lookup-based pattern (`analytic_f2` shares one query cache with `query_f1`, same documented deviation from
`Substrate`'s nominal contract as both existing substrates). Deliberately a single fidelity level (200
epochs) -- a real multi-fidelity ladder would add a second new variable alongside removing Θ, breaking the
isolation this experiment exists to provide. New tests follow the established real-data-skip convention
(`tests/test_substrates.py`'s `_requires_real_*` pattern) -- no fake/mock API stub, matching how the two
existing substrates are tested.

**Faza 3**: wired into `scripts/run_experiment.py`'s `_SEARCH_SPACE_BUILDERS`/`_SUBSTRATE_BUILDERS`; new
`configs/search_spaces/nas_bench_201.yaml` carries `default_grid: false` -- a genuinely separate, single-axis
experiment, not a third arm of the main ten/eleven-arm comparison grid. This required extending
`scripts/run_grid.py`'s `default_grid` opt-out mechanism (previously methods-only) to search spaces too, plus
a new `--budgets` CLI flag (`enumerate_grid` gained a `budgets` kwarg) -- both real, tested additions
(`tests/test_run_grid.py`), not just this one config's plumbing. Architecture docs
(`docs/architecture/c3/search-spaces-and-substrates.md`) updated with the third component.

**Faza 3.4 (smoke test) -- done.** Real NATS-Bench data (`NATS-tss-v1_0-3ffb9-simple`, ~1.15GB, the
lightweight archive) downloaded to `data/cache/nats_bench/` and verified end-to-end: `run_single` against
`nas_bench_201`/`random_search` at budget 5 returns real, plausible `(f1, f2)` pairs; all 8 previously-skipped
real-data substrate tests now run and pass.

**Real bug found and fixed during that verification**: `nats_bench.get_more_info` defaults to
`is_random=True`, which draws a uniformly random trial seed via Python's global `random` module on *every*
call, for any architecture with more than one logged trial -- confirmed directly (the same architecture
returned two different `test-accuracy` values across repeated default calls). This silently violated
`Substrate.deterministic=True` (`base.py`), a project-wide assumption. Fixed by passing `is_random=False`
explicitly (`substrates/nas_bench_201.py::_query`), which averages across the architecture's own logged
trials instead -- confirmed deterministic across 10 repeated queries, both directly and via a new regression
test (`test_nas_bench_201_query_f1_is_deterministic_across_repeated_queries`).

**New**: `scripts/run_nas_bench_201_isolation.py` -- a single entry point chaining smoke test -> full grid run
(R=30 seeds x 2 budgets x 2 methods = 120 runs) -> statistical analysis (Wilcoxon + Holm-Bonferroni + Cliff's
delta, `stats/significance.py`, scoped to `p3net` vs `random_search` per budget), so the user doesn't have to
run and report back on each step separately. Aborts before the expensive grid run if the smoke test fails.
Writes `results/nas_bench_201_isolation_result.md`. Deliberately does NOT edit `CHANGELOG.md`/
`conclusions.tex` itself -- writing the result into the paper's narrative, honestly, in either direction,
stays a manual step after the script finishes.

**Faza 4 (result) -- done, 2026-08-18.** User ran
`uv run python scripts/run_nas_bench_201_isolation.py` (R=30 seeds x {100, 350} budgets x {p3net,
random_search}, 120/120 real NATS-Bench queries, ~5m35s). Result (`results/nas_bench_201_isolation_result.md`):

| Budget | n | Median p3net | Median random_search | Adj. p | Cliff's delta | Reject H0 |
|---|---|---|---|---|---|---|
| 100 | 30 | 0.9851 | 0.9857 | 0.9515 | +0.016 | False |
| 350 | 30 | 0.9923 | 0.9918 | 0.7415 | +0.118 | False |

**Honest reading: the isolation hypothesis is not supported.** Removing the joint architecture+hyperparameter
genotype extension entirely -- architecture-only NAS-Bench-201, no $\Theta$ at all, the exact axis the fourth
candidate explanation in `conclusions.tex` singled out as untested -- still does not let P3Net separate from
`random_search`. Cliff's delta is small and positive at both budgets (P3Net nominally ahead), growing from
+0.016 to +0.118 with budget, but neither is remotely significant after Holm correction ($p_\text{adj}=0.95$,
$0.74$), and both medians are already near the ceiling (0.985-0.992 relative hypervolume) -- consistent with
(iii)'s small/unstructured-landscape account (`lopes2023nasbenchdesign`) rather than with the joint-genotype
dilution hypothesis this experiment was built to test. This weakens, not strengthens, the fourth candidate
explanation as the operative one: with the joint-genotype axis now held fixed at "removed entirely" and the
result unchanged, the mechanistically-independent (i)-(iii) account -- pyramid bootstrap dominance, additive-
only surrogate, and the benchmark family's own documented small-landscape ceiling -- looks like the more
load-bearing explanation of the three-plus-one. Written into `conclusions.tex`'s "Why the results are what
they are" paragraph as a direct, dated answer to the open question it raised.

### Investigated (full $R=30$ grid rerun under the Phase 2/3/4/5 fixes -- honest result: real, verified fixes, no headline significance gained, 2026-08-18)

Faza 6 of the pyramid/surrogate/MO-BOHB plan: `p3net`, `p3_absolute`, `mo_bohb`, and the new
`p3net_surrogate_interactions` arm were rerun across the full grid (4 search spaces $\times$ 4 budgets
$\times$ 30 seeds = 480 runs each). Pre-fix raw data archived to
`results/archive/p3absolute-mobohb-pre-fix_2026-08-18/` (`p3net`'s own pre-fix data was already archived to
`results/archive/p3net-pyramid-bootstrap-dominated_2026-08-17/` in the prior pass). `scripts/generate_report.py`
regenerated `results/tables/fixed_budget_summary.md` and all figures from the fresh data; a supplementary
analysis script (mo\_bohb vs.\ random\_search directly, `p3net_surrogate_interactions` vs.\ `p3net`, pyramid
bootstrap share, and calibration by level size -- none of which `fixed_budget_summary.md` reports on its own)
was run against the same fresh raw data.

Every fix below is independently confirmed correct at the unit-test/mechanism level (Phases 0-5, all still
green). None of them, individually or in combination, produces a new statistically significant result on this
grid. Reported as-is, not spun:

- **Pyramid fix (Phase 2) -- real, modest, confirmed at full scale.** Bootstrap-dominated share at budget 350
  is now $90.3\%$ (jahs\_bench\_201), $91.7\%$ (Colorectal), $92.4\%$ (Fashion-MNIST), $91.0\%$
  (NAS-HPO-Bench-II) -- down from the previously documented $93$--$94\%$, and consistent with the smaller,
  single-search-space spot-check reported earlier ($90.7\%$, NAS-HPO-Bench-II, 5 seeds). The number of distinct
  pyramid levels grown is unchanged (7 levels, sizes $\{2,4,8,16,32,64,128\}$). P3Net still does not separate
  significantly from `random_search` in any of the 16 (search-space, budget) cells (still 0/16, Holm-corrected)
  -- the fix moves the needle in the right direction without being large enough to flip significance on this
  benchmark family.
- **P3Absolute engine-sharing (Phase 3) -- confound closed, and the honest result is a null.** Now that
  `p3_absolute` shares P3Net's own (Phase-2-fixed) `Pyramid` engine, the P3Net-vs-P3+absolute-regressor
  comparison genuinely isolates the surrogate for the first time. Result: 0/16 cells reach significance either
  way. Once the population-engine confound is removed, this grid shows no measurable advantage of the relative
  surrogate over the absolute regressor.
- **Surrogate interaction features (Phase 4) -- real capacity, no grid-level benefit.** The added representational
  capacity is real and directly demonstrated (`test_include_interactions_lets_the_model_represent_a_non_additive_pattern`,
  a constructed AND-pattern the additive-only encoding cannot fit). On the real grid, `p3net_surrogate_interactions`
  vs.\ the Phase-2-fixed `p3net` baseline: 0/16 cells significant, effect sizes small and inconsistent in sign.
  The landscape's real epistasis, at this benchmark family's scale, apparently isn't large enough for the added
  capacity to matter for search outcomes, even though the surrogate can now represent it.
- **RidgeCV regularisation (Phase 2) -- did not resolve the level-16 calibration spike.** Recomputed
  `calibration_r2` by pyramid level size across the full grid (budget 350): level 16 remains dramatically the
  worst-calibrated level ($R^2=-4.71$, MSE $766.7$) against every other level (best: level 2, $R^2=+0.55$,
  MSE $85.2$; every level from 8 upward is calibration-negative, i.e.\ worse than predicting the mean true
  delta). The level-16-vs-best MSE ratio ($\approx 9\times$) sits squarely inside the originally-documented
  $6$--$19\times$ range -- RidgeCV, though the textbook remedy for small-sample linear instability, did not
  visibly narrow this gap in practice on real data.
- **MO-BOHB normalisation (Phase 5) -- mathematically correct, empirically inconclusive.** The scale-invariance
  fix is proven exactly (`test_tchebycheff_scalarize_is_invariant_to_objective_rescaling`). On the full grid,
  `mo_bohb` separates from `random_search` in 1/16 cells (jahs\_bench\_201\_colorectal, budget 350,
  $p_{\mathrm{adj}}=0.038$) -- and that one significant cell favours `random_search`, not `mo_bohb`
  ($\delta=-0.45$). The normalisation removed a real, provable defect in the scalarisation, but did not produce
  the separation-from-random-search the reference literature reports for MO-BOHB on comparable benchmarks.

**Data housekeeping**: `results/tables/p3net_variants_summary.md` is stale leftover from the earlier,
already-concluded design-decision ablation round (its source configs were deleted, "Config cleanup",
2026-08-17) -- `scripts/generate_report.py` does not regenerate it and never has; left in place as historical
record, not corrected by this pass. Also noted in passing: 7 stray raw files
(`p3net_kappa_sensitivity__*__fake_space__budget{10,12,20}.json`) sit under `results/raw/` outside the real
4-search-space/4-budget grid, apparently test-fixture leakage -- excluded from every analysis above by
construction (filtered to the real grid), not otherwise investigated or cleaned up in this pass.

### Added (surrogate interaction features -- Phase 4 of the pyramid/surrogate fix, single-axis ablation, 2026-08-18)

Addresses the additive-only representational limit documented in Results ("Diagnostics: surrogate
representational capacity") and Conclusions: `RelativeLinkageAwareSurrogate`'s
$\hat\delta_F(x,x') = w\cdot\mathrm{onehot}(x) - w\cdot\mathrm{onehot}(x')$ is provably restricted to additive,
no-interaction functions of the genotype coordinates -- in tension with linkage-guided crossover's own premise
that the variable groups it protects have a joint, not merely additive, effect on fitness.

`p3net.surrogates.relative_linkage_aware`: new `include_interactions: bool = False` field and
`_interaction_features(x, x_prime)` helper -- one binary "did coordinates $i$ and $j$ change together" column
per unordered coordinate pair ($\binom{n}{2}$ total, fixed regardless of the current linkage tree), appended to
the existing concatenated one-hot features when enabled. Deliberately the *simplest* interaction encoding that
adds real capacity, not a full per-value outer product: naturally self-scopes to whichever subset a given pair
actually differs within, since `fit()` only ever trains on pairs restricted to a single subset already
(`_matching_subset`) -- a coordinate pair outside that subset can never show both members changed at once for
that pair, so no separate subset bookkeeping is needed and the feature vector's length stays fixed. Chosen over
a model-class swap (RandomForest/GBM, the alternative scoped in the plan) specifically to keep the relative/
delta framing's data-efficiency advantage ($O(|\mathcal{H}_t|^2)$ training pairs from the same observations)
intact, and because the model class stays `sklearn.linear_model.RidgeCV` (Phase 2's own already-adopted
regularisation), not a heavier one whose fit cost against that same quadratically-growing pair count was
flagged as a real risk when this was first scoped.

New test proves the capacity gain directly, not just that the code runs: a small deterministic AND-pattern
(`f1` is $10$ only when two specific coordinates are *both* $1$, $0$ for every single-coordinate flip -- not
decomposable as $g(x_0)+h(x_1)$ for any $g,h$) is fit near-exactly with `include_interactions=True` and with
real, larger error with it `False` (`lib/tests/test_relative_surrogate.py`).

`p3net.methods.p3net.P3Net` gains `use_surrogate_interactions: bool = False`, threaded into
`RelativeLinkageAwareSurrogate(model_factory=self.model_factory, include_interactions=self.
use_surrogate_interactions)` inside `_sweep_proposals` -- default unchanged, so every already-published result
and `p3net.yaml`'s own behaviour are untouched. New `configs/methods/p3net_surrogate_interactions.yaml`
(`default_grid: false`, mirroring exactly the same now-retired pattern `p3net_analytic_cost.yaml`/
`p3net_cascade.yaml`/etc.\ used): otherwise identical to `p3net.yaml`, so this is tested against the
**Phase-2-fixed** `p3net` baseline (warm-start, hypervolume-contribution stall, `RidgeCV` all already wired
into every `method: p3net` config via `build_method`), not the pre-fix pyramid -- sequenced after Phase 2,
not combined with it, so any effect stays attributable to this one axis. No `build_method` change needed: the
new config reuses the existing `method: p3net` dispatch branch entirely via its own `params:`, the same
pattern `p3_alone_pop20.yaml` already established.

Smoke-tested against the real `nas_hpo_bench_ii` substrate (2 seeds, budget 100 -- not the full grid, which is
bundled into the Phase 2 rerun per Conclusions): runs to completion, finite objectives, `bootstrap_proposals`/
`mixing_proposals`/level counts in the same range Phase 2's own validation already found. Both test suites
green (lib: 120; experiments: 204, 2 skipped).

### Changed (P3Absolute shares P3Net's Pyramid engine -- Phase 3 of the pyramid/surrogate fix, 2026-08-18)

Closes the confound documented in Results ("Diagnostics: surrogate representational capacity") and
Conclusions: the Baselines paragraph describes P3+absolute-regressor as isolating "only the surrogate," which
was not actually true -- `methods.p3_absolute.P3Absolute` used a flat, fixed-size population (`population_size:
20`, full-population sweep every call, truncation by sorting on `objective_index`), not `p3net.search_engines.
p3.pyramid.Pyramid`, so any P3Net-vs-P3+absolute gap mixed a surrogate-formulation difference with a
population-management one.

`P3Absolute` rewritten to mirror `p3net.methods.p3net.P3Net`'s own `propose`/`update`/`_bootstrap_proposals`/
`_sweep_proposals`/`_update_level_population` shape exactly, including the warm-start and hypervolume-
contribution changes from Phase 2 above, substituting `AbsoluteRegressorSurrogate` for
`RelativeLinkageAwareSurrogate` and keeping its existing absolute (not telescoped) acceptance rule (`predicted
<= current_value`) unchanged -- no telescoping construction is needed for a surrogate that predicts f1
directly. `configs/methods/p3_absolute.yaml`: `population_size: 20` -> `growth_factor: 2` (P3Net's own
default, deliberately matching it rather than picking a separate value, so the two arms' population dynamics
are genuinely comparable). Also gained `bootstrap_proposals`/`mixing_proposals`/`population_snapshots` --
the three Phase 0 diagnostics that verify the engine swap itself took effect, not just a renamed constructor
argument -- but not `chain_depth_log`/`level_size_log`/the fit-timing fields, which assume P3Net's telescoping
construction specifically.

New tests confirm the swap directly (`test_p3_absolute_shares_p3nets_own_pyramid_engine_not_a_flat_population`:
a real `Pyramid` instance, growing over a long run exactly like P3Net's own does, all three diagnostics
populated; `test_persist_run_includes_pyramid_diagnostics_for_p3_absolute`: the JSON round-trip carries them,
and confirms the telescoping-specific fields are correctly absent). Both test suites green (lib: 117;
experiments: 203, 2 skipped).

**Not yet reflected in the published numbers**: Results' fixed-budget tables and the "surrogate representational
capacity" caveat still describe the old, unshared-engine `P3Absolute` -- re-running it is bundled with the
Phase 2 pyramid fix's own full-grid rerun (Conclusions), not done separately, since both changes affect the
same raw data and a rerun would otherwise happen twice.

### Investigated (literature-grounded pyramid strengthening attempted, reverted after a real regression, 2026-08-18)

Follow-up to the Phase 2 pyramid fix's own validation (below), which showed only a modest bootstrap-share
improvement (median $90.7\%$ vs.\ the documented $93$--$94\%$ pre-fix baseline, level count unchanged at 8
for budget 350). Checked whether canonical P3 itself has a mechanism this implementation is missing,
deliberately grounded in literature rather than tuned against these four benchmarks specifically.

Confirmed directly (`goldman2014parameterless`'s own description, cross-checked via several independent
secondary sources -- the primary PDF is not text-extractable in this environment): canonical P3 does **not**
bootstrap an entire `growth_factor^k`-sized level with pure random individuals before any mixing begins. It
generates **one** new individual at a time, locally improves it via First-Improvement Hill Climbing, then has
it climb the pyramid -- optimal-mixed against level 0 first, promoted and tried against level 1 if it
improved there, and so on, cascading upward in a single pass. Levels grow organically, one accepted
individual at a time; there is no upfront batch-fill step at all.

Implemented the closest matching change: lowered the bootstrap-to-mixing transition from `level.size` (the
full, possibly huge geometric target) to `growth_factor` (level 0's own natural size -- already this
project's only real parameter, no new one introduced), so every level starts real, guided search almost
immediately rather than after an exponentially-growing random batch.

**Reverted after direct testing found a severe regression, not merely a smaller-than-hoped effect.** The
existing 150-budget test in `lib/tests/test_p3net_pyramid_integration.py`, unrelated to this specific change,
caught the pyramid growing past level 90 (`level_size_log` containing $2^{96}$) within a single short test
run -- versus 8 levels total at budget 350 under the already-validated Phase 2 baseline. Root cause: unlike
canonical P3's single-individual FIHC, this implementation's linkage-tree-guided optimal-mixing sweep needs a
real donor pool to produce anything. At a population of 2 (`growth_factor`), a sweep pass degenerates almost
immediately into `_sweep_proposals`'s own zero-new-candidates stall fallback (a single random point), which
then rarely clears `Pyramid.promote`'s hypervolume-contribution bar against a population of only 2, stalling
the level and triggering the next one. Because every level, regardless of its own eventual cap, only ever
needed `growth_factor` individuals to exit bootstrap under this change, the pyramid could cycle through dozens
of levels for a handful of evaluations each, rather than doing sustained search at any one reasonably-sized
population -- a different, more computationally severe version of the same underlying problem this whole
investigation started from, not a fix for it. Confirming this empirically before keeping it, rather than
assuming a literature-matched change would simply work, is exactly why this was caught before landing anywhere
near a real experiment run.

**Not pursued further with a larger, hand-picked constant in place of `growth_factor`**: choosing one that
happens to avoid this pathology on these four benchmarks specifically, with no principled way to derive it,
would be exactly the kind of dataset-specific tuning this investigation was explicitly trying to avoid.
Reverted in full -- `P3Net.propose`/`_update_level_population`/`_bootstrap_proposals` all back to using
`level.size` as the bootstrap-to-mixing threshold, matching the already-validated Phase 2 state exactly; both
test suites confirmed green and back to their pre-attempt runtime (117 lib tests in ~11s, not the ~97s the
runaway case took). Left as a genuinely open direction for a future pass: a donor-pool-aware minimum
population (scaled to what optimal mixing actually needs to be non-degenerate, not a bare constant) is the
natural next candidate, not attempted here.

### Investigated (surrogate magnitude calibration and telescoping chain-depth error accumulation, 2026-08-18)

Follow-up prompted by a direct question about whether $\hat\delta_F$'s *magnitude* predictions are
trustworthy, not just their sign (already covered by the acceptance-gate-precision investigation and
"Diagnostics: surrogate representational capacity" above). New metric
`metrics.surrogate_quality.calibration_r2` ($R^2$ of predicted vs.\ true delta), run first against the
already-logged `surrogate_quality_log` data (archived `p3net` run, 2026-08-17), then followed up with new,
real instrumentation:

1. **Magnitude calibration is dramatically negative in every search space** -- jahs_bench_201 (CIFAR-10):
   $R^2=-51.34$; jahs_bench_201_fashion: $-30.71$; jahs_bench_201_colorectal: $-12.88$; nas_hpo_bench_ii:
   $-1.64$ -- markedly worse than trivially predicting the mean true delta, everywhere. Does **not** track
   the epistasis ordering established for sign-agreement and the ablation-family wins (worst on CIFAR-10,
   least-bad on NAS-HPO-Bench-II): this complicates, rather than confirms, that earlier account for the
   magnitude dimension specifically.

2. **Binned by $|\mathcal{H}_t|$** (same binning `reporting.plots.surrogate_quality_figure` already uses):
   the badness is not uniform over a run. Early predictions ($|\mathcal{H}_t|=2$--$30$) are calibrated
   reasonably ($R^2$ up to $+0.17$ on jahs_bench_201, $+0.07$ on nas_hpo_bench_ii); a narrow window
   ($|\mathcal{H}_t|\approx30$--$58$) is catastrophic ($R^2$ as low as $-227$ on jahs_bench_201) with the
   single worst point in **every one of the four search spaces** landing at $|\mathcal{H}_t|=35$--$40$; later
   bins recover to "merely bad" ($-1$ to $-20$).

3. **New `P3Net.chain_depth_log`** (parallel list to `surrogate_quality_log`, added specifically for this
   investigation, one telescoping chain length per logged prediction -- `implementation/lib/src/p3net/
   methods/p3net.py`, tested in `lib/tests/test_p3net_pyramid_integration.py`), checked against 5 fresh real
   seeds on the real `nas_hpo_bench_ii` substrate at budget 350 (not a toy problem): squared error grows
   monotonically with chain depth -- median $12.96$ at depth 1 to $744.80$ at depth 5 ($n=5$--$38$ per depth
   bucket); every one of the 10 single worst logged predictions has chain depth $\geq3$, none $\leq2$.
   Confirms `telescoped_estimate`'s error-accumulation mechanism (`p3net.surrogates.telescoping`: one
   $\hat\delta_F$ call summed per chain step) is real and substantial, not merely a theoretical concern.
   **Does not fully explain the $|\mathcal{H}_t|\approx30$--$58$ window specifically**: chain depth there is
   only mildly elevated versus outside it (median $4.5$ vs.\ $4.0$, both capped at $\kappa=6$ for this
   search space) -- something in addition to chain length is making that window worse, not yet identified.

4. **Isolated to one specific pyramid level, not a general property.** Squared error by the sweeping
   level's own target size, same 5 seeds: level sizes 2/4/8 median $67.8$--$117.6$; **level size 16: median
   $1307.29$** ($6$--$19\times$ every other size); level sizes 32/64/128 back down to $130.5$--$220.2$. The
   level whose first sweep-based (surrogate-scored) predictions land at $|\mathcal{H}_t|\approx33$--$36$ in
   \emph{all five seeds} -- matching finding 2's window exactly. 9 of the 10 single worst logged predictions
   have level size 16. New `P3Net.level_size_log` (same parallel-list pattern as `chain_depth_log`, tested
   alongside it).

5. **Plausible mechanism, not confirmed further.** Level size 16's linkage tree is built from that level's
   own population, freshly and purely-randomly bootstrapped the moment this sweep phase begins. If it
   proposes linkage subsets not yet well represented among the (still few, $\approx30$) matching pairs
   available in $\mathcal{H}_t$ for the one shared linear model to fit, extrapolation for those specific
   one-hot coordinates is the expected consequence. Not confirmed by directly measuring matching-pair counts
   per subset at fit time -- the natural next step if this needs fully closing, not done here.

6. **Literature check on established remedies for this class of failure** (surrogate point-estimates
   trusted without regard to their own reliability): the dominant approach in the surrogate-assisted
   evolutionary computation literature couples model management with explicit uncertainty -- MSE/EI/LCB/PoI
   infill criteria over models that report their own confidence, and trust-region/local-model restriction to
   avoid extrapolating far from training data~\citep{jin2011surrogate}. The closest already-cited prior work
   facing the same class of problem, CS-GOMEA, moved to a strictly more expressive model (a CNN, also
   trained on pairwise fitness differences, for the same evaluation-efficiency reason as $\hat\delta_F$)
   rather than regularising a linear one~\citep{dushatskiy2019csgomea}. Ridge
   regression~\citep{hoerl1970ridge} is the standard, cheaper first-line defence specifically for "small-
   sample, unstable, high-variance linear fit" -- targets the *symptom* (extreme coefficient/prediction
   magnitude) directly, regardless of whether finding 5's exact mechanism is fully right, without changing
   $\hat\delta_F$'s additive-only representational capacity (Diagnostics: surrogate representational
   capacity, above) at all -- a different, complementary axis, not a substitute for that finding's own
   candidate fix.

**Adopted into the pyramid-fix implementation pass (plan, "Faza 2")**: `RelativeLinkageAwareSurrogate`'s
`model_factory` moves from `sklearn.linear_model.LinearRegression` to `sklearn.linear_model.RidgeCV`
(regularisation strength selected automatically via built-in cross-validation, not hand-tuned, so this does
not add a real new hyperparameter) alongside the warm-start/hypervolume-contribution changes -- bundled with
the pyramid-transition redesign rather than staged as a separate pass, since both concern exactly the same
moment (a level's first sweep pass after its own bootstrap), and that fix's own validation step is the
natural place to check whether the level-size-16-specific spike also shrinks as a result.

### Fixed (citation-accuracy sanity check against baseline literature, 2026-08-17)

Literature sanity check on whether the paper's own baseline results match the literature those baselines
come from, prompted directly by a question about it. Found and fixed one citation-accuracy issue in
`chapters/v003/related_work/main.tex`:

- **`guerreroviu2021bagofbaselines` was not tested on JAHS-Bench-201 or NAS-HPO-Bench-II.** The prior text
  read "SH-EMOA and MO-BOHB were established specifically for joint architecture and hyperparameter search
  on these same two benchmarks," which a literal reading attributes their own evaluation to P3Net's two
  benchmarks. Checked directly: the paper's own text and its code repository
  (`github.com/automl/multi-obj-baselines`, README) both confirm its evaluation uses a custom search space
  (Oxford-Flowers, Fashion-MNIST at 16x16), not JAHS-Bench-201 or NAS-HPO-Bench-II -- and could not have,
  since arXiv 2105.01015 (May 2021) predates both NAS-HPO-Bench-II (arXiv 2110.10165, October 2021) and
  JAHS-Bench-201 (NeurIPS 2022) by publication date alone. Reworded to attribute what is actually true and
  well-supported -- SH-EMOA and MO-BOHB were established for the joint-setting *problem*, not tested on a
  benchmark shared with this project -- and to state plainly what their own evaluation used instead. No
  residual claim depends on the removed, unverified benchmark-sharing detail.
- **Not a code or experiment issue.** This is a citation-precision correction to Related Work's framing of
  *why* SH-EMOA/MO-BOHB were adopted, not a claim about how they are implemented or evaluated in this
  project's own harness -- `methods/sh_emoa.py` and `methods/external/mo_bohb.py` are unaffected, and no
  experiment needs rerunning because of this specific finding.
- **Positive corroboration found in the same pass**: `guerreroviu2021bagofbaselines`'s own results (Table 3)
  show MO-BOHB clearly and consistently beating random search (e.g. hypervolume 317.98 vs.\ 299.05 on their
  Flowers benchmark, 441.86 vs.\ 393.86 on Fashion-MNIST) and SH-EMOA doing the same. In this project's own
  grid, SH-EMOA shows the same pattern (12 of 16 cells significantly beat `random_search`, the strongest of
  any arm), consistent with the reference literature -- but MO-BOHB does not (1 of 16), inconsistent with it.
  This is independent, literature-based corroboration for the MO-BOHB Tchebycheff-scalarisation concern
  raised separately (below, "surrogate representational capacity" entry's sibling discussion) -- two
  different lines of evidence (internal code/measured-scale analysis, and now external comparison against
  the algorithm's own source paper) now point the same way, rather than one analyst's judgement call.

### Investigated (per-dataset win/loss pattern traced to population-pyramid bootstrap dominance, 2026-08-17)

Follow-up to the two investigations below (result variance/IQR, acceptance-gate precision), neither of
which cleanly explained why P3Net's ranking among the eleven arms is strongest on Fashion-MNIST, partial
on CIFAR-10, and erodes with budget on Colorectal-Histology and NAS-HPO-Bench-II (Results, "Fixed-budget
summary" / "Scope, and what would extend it"). Three further hypotheses tested, one dispatched to a
throwaway analysis script per hypothesis (none committed), findings independently spot-checked against
the project's own `reporting`/`stats` pipeline rather than taken on faith:

1. **Pareto front geometry per dataset -- REJECTED.** Correlation, front curvature, point count, and
   front "thickness" were measured on the full pooled (11 methods x 30 seeds) evaluation cloud per search
   space at budget 350. All four search spaces have the same extreme convex front shape; Fashion-MNIST
   and Colorectal-Histology (P3Net's best and worst datasets) are statistically indistinguishable on every
   geometric measure tried. One raw-unit "front thickness" metric did match the ranking, but the C* acceptance
   gate (`p3net.methods.p3net.P3Net._sweep_proposals`, step 4: `pareto_front` in estimated (f1, f2)) only
   ever compares with `<=`/`<` (`problem/objectives.py::dominates`), so it is provably invariant to any
   monotone rescaling of f1/f2 -- confirmed by quantile-transforming both objectives (preserves the
   dominance structure exactly) and watching the "match" disappear. A direct simulation of gate reliability
   under realistic surrogate error ran in the *opposite* direction to the hypothesis: least reliable on
   Fashion-MNIST (where P3Net does best), most reliable on NAS-HPO-Bench-II (where it does worst).

2. **Competing-algorithm mechanism -- CONFIRMED, and the primary driver.** P3Net's own population pyramid
   (`p3net.search_engines.p3.pyramid.Pyramid`) grows levels geometrically
   (`add_level`: `size = growth_factor ** (len(levels) + 1)`, i.e. 2, 4, 8, ..., 256 at
   `growth_factor=2`), starts every new level from an **empty population**, filled only by
   `P3Net._bootstrap_proposals` -> `_diversity_injection` -> `search_space.sample_uniform` (uniform
   random, no elites carried over), and grows to a new level as soon as `Pyramid.all_stalled` -- which,
   because only the newest level is ever swept (`P3Net.propose`/`update` always act on `self._level`,
   the last level in the list; a documented simplification, `p3net.methods.p3net` module docstring,
   simplification 1), degenerates to "the newest level failed once to strictly Pareto-dominate its own
   incumbent" (`Pyramid.promote`). Since each new level is larger than the sum of every level before it
   (geometric growth), this structurally forces the *uniform-random-bootstrap* share of the total budget
   to **rise**, not fall, as the budget grows. Instrumented replay (10/10 seeds reproduced the persisted
   `results/raw/` payloads byte-for-byte) measured this directly on NAS-HPO-Bench-II: bootstrap share
   81.6% -> 86.6% -> 90.8% -> 93.0% at budgets 50/100/200/350; mixing(sweep)-driven share falls
   16.2% -> 12.3% -> 8.7% -> 6.7% over the same range. Cross-checked via the persisted
   `surrogate_quality_log` (only mixing-driven, surrogate-scored proposals are ever logged there, by
   construction -- field docstring, `p3net.methods.p3net.P3Net.surrogate_quality_log`) across all four
   search spaces at budget 350: 6.9% (CIFAR-10), 6.6% (Colorectal), 6.3% (Fashion-MNIST),
   6.9% (NAS-HPO-Bench-II) mixing-driven -- flat across datasets, confirming the mechanism itself has
   no dataset-dependent term (only the pyramid's own geometry does).

   Behavioural consequence, verified independently against the already-published
   `results/tables/fixed_budget_summary.md` and re-derived from scratch via `reporting.tables._run_metric`
   / `stats.significance.cliffs_delta` (not the throwaway script that first found it): **P3Net is not
   statistically distinguishable from `random_search` in any of the 16 (search-space, budget) cells**
   (every `random_search` row in the summary table already shows `reject_null=no`; independently
   recomputed |Cliff's δ(P3Net, random_search)| is between 0.02 and 0.23 everywhere, nowhere
   significant). Consequently, P3Net's Cliff's-δ margin against *any* of the five differently-
   engineered baselines (SH-EMOA, TPE, NSGA-Net, NSGANetV2, MO-BOHB) tracks that baseline's own margin
   against `random_search`, computed independently per (search space, budget, baseline), n=80:
   Spearman ρ=0.962 (p=1.1e-45), Pearson r=0.965. Since how much any guided
   method beats `random_search` by is itself dataset-dependent (mean δ(random_search,
   4 guided baselines) at budget 350: Fashion-MNIST -0.211, CIFAR-10 -0.789, Colorectal
   -0.734, NAS-HPO-Bench-II -0.868), this single mechanism explains both the *budget* trend (the
   guided-vs-bootstrap ratio between P3Net and its competitors diverges monotonically, 3.7x at
   budget 50 to 14.2x at budget 350 on NAS-HPO-Bench-II) and the *dataset* trend (Fashion-MNIST is
   simply the search space where guided search barely beats uniform sampling at all, so a
   near-random-search method loses least there) without needing a second, dataset-specific mechanism.
   MO-BOHB is the one baseline P3Net does not consistently lose to; its own guidance is independently
   broken (`hpbandster.BOHB`'s default `random_fraction=1/3`, permanent, plus
   `methods/external/mo_bohb.py`'s Tchebycheff scalarisation drawing fresh, unnormalised random weights
   on every report -- on NAS-HPO-Bench-II f2 is roughly 19x f1's scale, so the unweighted `max()`
   is dominated by cost almost always, and only 4-8% of its "good" KDE training set is actually
   Pareto-nondominated).

   Successive halving as an alternative explanation was checked directly in code and ruled out: neither
   SH-EMOA nor MO-BOHB implements early rejection in this harness (`methods/sh_emoa.py` is a plain
   (mu+lambda) EMOA; `methods/external/mo_bohb.py` pins `FIXED_BUDGET = 1.0`, no fidelity escalation).

3. **Linkage-tree / genotype dependency structure per dataset -- REJECTED as originally framed; a sharper,
   related finding CONFIRMED instead.** Rebuilt actual linkage trees (`search_engines.p3.linkage_tree`)
   from real `p3net` budget-350 populations, 30 seeds x 4 search spaces: subset-size distribution,
   fraction of high-order (>=3) subsets, and population mutual information above an i.i.d.-uniform
   null are all statistically indistinguishable across datasets (consistent with finding 2 above -- a
   tree built mostly from a level's own uniform-random bootstrap clusters mostly noise; NAS-HPO-Bench-II,
   where P3Net loses most, has if anything the *largest* excess MI, opposite the naive hypothesis).
   Reframed the question from "how much dependency" to "where it sits, relative to what the surrogate can
   represent": `p3net.surrogates.relative_linkage_aware.RelativeLinkageAwareSurrogate.fit` trains
   `sklearn.LinearRegression` (`scripts/run_experiment.py::build_method`, `model_factory=LinearRegression`
   for `p3net`) on `X = onehot(x) ⊕ onehot(x')`, `y = f1(x) - f1(x')` -- a linear model on concatenated
   one-hot endpoints can only represent delta_hat_F(x,x') = w·onehot(x) - w·onehot(x'), an antisymmetric,
   strictly *additive* (no-interaction) function of the genotype coordinates, confirmed empirically
   (corr(w_left, -w_right) = 1.0000 exactly, 40/40 real fits, 10 seeds x 4 search spaces). A held-out-CV
   measure of "architecture-involving epistasis" (R² gained by adding 2nd-order interactions touching >=1
   architecture edge, over a main-effects-only model of f1) is flat in total (0.40-0.50 across all four
   search spaces) but its *location* moves monotonically, non-overlapping ranges across all four datasets,
   in exactly the order of where P3Net's win over its own no-surrogate ablations (`p3_alone`,
   `p3_alone_pop20/40`, `p3_absolute`) is strongest to weakest: Fashion-MNIST -0.020 (near-perfectly
   additive; P3Net wins at every budget), CIFAR-10 +0.034, Colorectal-Histology +0.102, NAS-HPO-Bench-II
   +0.250 (P3Net's ablation wins disappear and invert at budget 350). 98% of real P3Net moves touch an
   architecture edge, so this misspecification is the dominant, not a marginal, error mode. Causal
   attribution (that this specifically is what destroys the surrogate's benefit on those datasets, not
   merely correlates with it) was not tested interventionally and is flagged as unverified.

**Deepening pass on the just-completed kappa/acceptance-threshold sensitivity sweep** (see "Surrogate
error accumulation" below, now complete): does retuning either knob change the bootstrap-dominance finding
above? No. Pooled across the full kappa x threshold grid (12--16 cells x 30 seeds, all four search
spaces), the mixing-driven share of budget 350 is 6.0-7.1% median in every cell (range
3.4-12.6%), matching the headline `p3net` arm's own 6.3-6.9% almost exactly; fixed-budget
hypervolume (own-run reference point) varies by only 0.08-0.68% relative spread across the entire
12-cell grid per search space at budget 350. Surrogate rank correlation (Spearman, predicted vs. true
delta) is modestly positive everywhere (0.14-0.41) but, consistent with the already-closed
acceptance-gate-precision investigation, does not track the per-dataset outcome ranking: NAS-HPO-Bench-II
has the *highest* rank correlation of the four search spaces (0.29-0.41) despite the worst fixed-budget
outcome. Both kappa and acceptance-threshold are therefore ruled out as an alternative fix for finding 2
above -- the bootstrap-dominance mechanism is structural to `Pyramid`'s growth rule, not a symptom of
poorly-tuned surrogate hyperparameters.

**Data housekeeping**: the headline `p3net` arm's 480 raw runs (`results/raw/p3net__*.json`) reflect the
pyramid-growth-dominated behaviour documented above and are no longer the results a rerun under a fixed
pyramid would produce. Archived, not deleted, to
`results/archive/p3net-pyramid-bootstrap-dominated_2026-08-17/` (flat file layout, matching
`p3net-pre-analytic-cost_2026-08-17`'s precedent, not `scripts/archive_snapshot.py`'s `raw/`-subfolder
convention, since only one method's files moved). `results/raw/` now has no `p3net__*.json`;
`results/tables/`, `results/figures/`, and this draft's own numbers are left exactly as they were computed
against the archived data -- **not** regenerated -- since a pyramid fix is proposed for discussion, not
implemented, in this pass (Conclusions). Every other `p3net_*` method family (`p3net_cascade`,
`p3net_kappa_*`, `p3net_threshold_*`, `p3net_transient_donors`, `p3net_f1_truncation`,
`p3net_grow_on_stall`) shares the identical `Pyramid`-based engine and is equally affected, but those
raw files were left in place: the design-decision-ablation-round ones are already historical (their
configs were deleted once resolved, "Changed", 2026-08-17 below) and the sensitivity-sweep ones
(`p3net_kappa_sensitivity__*`) are not part of `MAIN_COMPARISON_METHODS` and block nothing.

### Investigated (surrogate representational capacity -- structural account and manuscript propagation, 2026-08-17)

Follow-up to finding 3 of the investigation directly above (linkage-tree/genotype dependency structure),
whose empirical result -- $\hat\delta_F$ is provably additive/no-interaction (confirmed:
corr(w_left, -w_right) = 1.0000, 40/40 real fits) and its measured "architecture-involving epistasis" proxy
tracks the per-dataset ablation-win ordering -- was recorded in this file but had not yet been carried into
`chapters/v003/results/main.tex` or `conclusions/main.tex`; grep confirmed neither file mentioned
"epistasis", "additive", or `LinearRegression` before this pass. Closed that gap and extended the finding in
three ways, each verified directly against source rather than re-asserted from the earlier pass:

1. **Scope clarification (new).** The same model class -- `sklearn.LinearRegression` over a plain one-hot
   encoding, no interaction terms -- is not unique to `RelativeLinkageAwareSurrogate`
   (`p3net.surrogates.relative_linkage_aware`). `AbsoluteRegressorSurrogate`
   (`p3net.surrogates.absolute_regressor`, its own docstring: "Used by ../methods/nsganetv2.py and
   ../methods/p3_absolute.py; both must use the same model family so the P3-vs-NSGA-II ablation isolates the
   search engine, not the surrogate") uses it too, and `scripts/run_experiment.py::build_method` wires
   `model_factory=LinearRegression` identically for `p3net` (line 147), `p3_absolute` (line 159), and
   `nsganetv2` (line 170). The additive-only limitation is therefore shared by every surrogate-based arm in
   the grid, not specific to the relative/delta formulation -- it cannot, by itself, explain a difference
   between P3Net and its own P3+absolute-regressor or NSGANetV2 comparisons (Fixed-budget summary), only why
   any of the three surrogate-based arms' benefit over their no-surrogate counterparts is inconsistent
   across datasets.

2. **Population-engine confound (new).** `methods.p3_absolute.P3Absolute` (the P3+absolute-regressor
   ablation) does not reuse `Pyramid` at all -- it is a fixed `population_size=20`, sweeps every member every
   call, and replaces by truncation on the objective value (`p3_absolute.py`, no `growth_factor`, no
   `_stalled`, no bootstrap-share pathology). Checked directly against the same throwaway relabeling script
   used for the random-search breadth check below: `p3_absolute` rejects "indistinguishable from
   random_search" in 10 of 16 cells, versus `p3net`'s 0 of 16 -- consistent with, though not proof of, most of
   that gap coming from which population engine is used rather than from relative-vs-absolute prediction per
   se. Any reading of the existing P3Net-vs-P3+absolute-regressor comparisons (Fixed-budget summary; Design
   decisions) as isolating "the surrogate alone," per the Baselines paragraph's own framing, should be
   qualified accordingly.

3. **Structural argument (new).** Linkage-guided crossover exists specifically because the linkage tree has
   detected variable groups whose *joint* effect on fitness is not the sum of their individual effects
   (`chapters/v003/related_work/main.tex`: "protecting detected groups of dependent variables from being
   disrupted") -- a purely additive landscape would need no linkage tree at all, since a single-coordinate
   hill-climber would already find the optimum. Scoring exactly those linkage-guided, multi-coordinate
   proposals with a model that is mathematically blind to any interaction among the coordinates it groups
   together is a structural tension in the current design, not a tuning gap. This sharpens finding 3's
   correlational epistasis-ordering result into a mechanistically motivated one; still not tested
   interventionally.

4. **Related-work contrast (new).** Neither of the two search-time, linkage-aware surrogates P3Net is
   positioned against in Related Work shares this specific failure mode. Bartnik's absolute regressor is
   deliberately fit as one of several nonlinear-capable families (SVR, MLP, random forest, gradient
   boosting), so an interaction is representable regardless of her linkage mechanism. eLyMPuS is not a
   regression over a concatenated encoding at all -- a discrete better/worse/ambiguous comparison tied to
   its own recursive linkage discovery, under a monotonicity assumption P3Net's own adaptation already
   declines to import (Related Work, existing text). $\hat\delta_F$'s combination -- linear, and fit over the
   flat concatenated encoding rather than routed through the linkage tree's own subset structure -- lands
   closer to what CS-GOMEA's own authors already flag as an open problem in their differently-shaped
   surrogate: a model that doesn't exploit linkage tree information in its own construction.

**Also computed, prompted by a direct question about how common P3Net's own zero-of-sixteen record against
`random_search` (finding 2 above) actually is**: a throwaway script (not committed) reused
`reporting.tables.fixed_budget_summary_table` unchanged, relabeling `random_search` as the reference arm and
the real `p3net` as a plain baseline in memory only (no files touched), to get the identical per-cell
Holm-corrected treatment for all ten non-`random_search` arms against it. Cross-checked against the already-
published table: `p3net`-vs-`random_search` Cliff's $\delta$ at (JAHS-Bench-201, budget 350) comes out
$-0.176$ here against $+0.176$ in `results/tables/fixed_budget_summary.md`'s P3Net-referenced row -- an exact
sign flip, as expected from swapping which arm is the reference, confirming the relabeling didn't change the
underlying paired samples. Result: 67 of 160 cells (42%) reject "indistinguishable from random_search" across
the whole grid -- not a rare event -- but per arm the counts range from SH-EMOA (12/16) and P3-alone (11/16)
down through NSGANetV2 (9/16), P3+absolute-regressor (10/16), the P3-alone population variants (7/16 and
6/16), NSGA-Net (6/16), and TPE (5/16), to MO-BOHB (1/16, consistent with finding 2's own broken-guidance
account) and **P3Net (0/16)**. Every arm except MO-BOHB clears random search significantly in at least 5 of
16 cells; P3Net never does. `chapters/v003/results/main.tex`'s "Diagnostics: population-pyramid bootstrap
share" paragraph gets a short addendum reporting this; the full per-cell detail lives only in this
investigation's (uncommitted) script output, not in the manuscript.

`chapters/v003/results/main.tex`: new `\paragraph{Diagnostics: surrogate representational capacity.}`,
inserted after the P3-alone sweep-completion table and before "Scope, and what would extend it."
`chapters/v003/conclusions/main.tex`: new bullet (11th), parallel to the pyramid-finding bullet,
forward-referencing this paragraph and flagging it as a second, independent candidate direction for
follow-up. No code changed in this pass -- documentation only, per this round's explicit scope.

### Investigated (acceptance-gate precision regression under analytic_cost, 2026-08-17)

Adopting `analytic_cost` (see below) improves fixed-budget hypervolume but collapses
`p3net.methods.p3net.P3Net.surrogate_quality_log`'s own pairwise sign-agreement measure from
`0.672` (pre-adoption default, matching the `0.62`--`0.75` range an earlier draft of
`chapters/v003/results/main.tex` reported) to `0.497` (essentially chance) pooled across the
full R=30, four-dataset, four-budget grid. Four rounds of matched-seed investigation, each
building throwaway instrumentation (subclassing `P3Net`, never committed) rather than
speculating from aggregate stats alone:

1. **Not a logging/selection artefact.** `analytic_cost` only ever affects `f2`; a direct trace
   confirmed the telescoped `f1` estimate for a given candidate is byte-identical whether or not
   it is enabled.
2. **Not accumulated chain error.** Mean accepted chain length is, if anything, shorter under
   the new default (4.05 vs. 4.65 across 5 matched seeds on NAS-HPO-Bench-II); degradation is
   present at every chain length, not concentrated in long chains.
3. **Not a worse-fitting surrogate.** In-sample R² on the model's own training pairs is
   essentially unchanged (0.85--0.99 either way, 0 negative-R² iterations in either condition).
4. **Not extrapolation distance from the training data.** Distance to the training centroid and
   to the nearest training pair are statistically indistinguishable between the two defaults;
   degradation is uniform across near and far candidates alike.
5. **What actually explains it**: `surrogate_quality_log` only ever records *accepted*
   (predicted-improvement) modifications by construction (step-3's acceptance gate rejects
   predicted declines before they can be logged) -- confirmed via a confusion-matrix check:
   100% of logged predictions are "positive" under both defaults, 0 true/false negatives
   possible in either. The metric therefore measures the acceptance gate's *precision*, not a
   symmetric classification accuracy with a meaningful 0.5 floor. Once C\* selection
   (nondomination in `(f1, f2)`) has a genuinely-varying `f2` instead of a near-constant
   inherited one, it starts promoting candidates for a good `f2` as often as for a confident
   `f1` prediction -- a direct sweep-by-sweep trace shows the two defaults' evaluated-genotype
   sequences, identical through the bootstrap phase, diverging as early as the 4th
   sweep-based decision on a matched seed.

`chapters/v003/results/main.tex`'s Surrogate quality paragraph is corrected to describe the
metric as acceptance-gate precision (this correction applies regardless of which default is
active -- the pre-adoption default's own `0.62`--`0.75` claim was the same metric, just not
named accurately), reports the actual current number, and forward-references the full
investigation in the new "Design decisions" paragraph. Why a lower-precision gate coexists with
a better downstream hypervolume result is flagged as a genuinely open question in Conclusions,
not resolved here.

### Changed (P3Net design-decision ablation round resolved, 2026-08-17)

Following the R=30, 4-dataset x 4-budget combined run of the eleven main
arms plus nine `p3net_*` design-choice ablation configs, analyzed each
against baseline `p3net` (144 comparisons, Holm-Bonferroni corrected per
cell):

- **Adopted: `analytic_cost` always wired.** `use_analytic_cost` is gone
  as an opt-in config marker; `scripts/run_experiment.py::build_method`
  now unconditionally passes `substrate.analytic_cost_objectives` into
  `P3Net.analytic_cost` for every `p3net` config. Evidence: effect
  favoured analytic cost in 15/16 (search_space, budget) cells, reaching
  significance on Fashion-MNIST at budget 200 (p=0.0012) and 350
  (p=0.0034), with a strengthening dose-response pattern and tighter
  variance, at essentially zero extra cost. This also fixes a real
  discrepancy: `chapters/v003/proposed_optimizer/main.tex`'s
  "Deduplication" paragraph already stated f2 "is computed analytically"
  -- the shipped default previously inherited it from the ancestor
  instead.
- **Not adopted, deferred: `cascade`.** One significant win (Colorectal
  budget 200, p=0.0168), directionally favourable on Colorectal/
  NAS-HPO-Bench-II overall, but neutral-to-negative on CIFAR-10 and
  notably (non-significantly) worse on Fashion-MNIST budget 50 -- plus a
  real per-iteration compute cost (surrogate refit and linkage tree
  rebuilt once per active level, not once total). Left as a candidate for
  a dedicated, better-powered follow-up rather than a default.
- **No change: `truncation`, `stall_recovery`, `donor_pool`, `kappa`
  (half/double spot-checks), `acceptance_threshold` (permissive/strict
  spot-checks).** Zero significant differences anywhere in the remaining
  ~128 comparisons. Kept exactly as originally designed (`pareto`,
  `reinject`, `h_t_only`, `kappa=2*ceil(log2(n))`,
  `acceptance_threshold=0`). This closes two open points:
  `proposed_optimizer/main.tex`'s "Parent, donor, and ancestor
  provenance" TODO (donor pool tested, no difference, `h_t_only` kept)
  and the previously-unstated population-truncation rule (tested, no
  difference, `pareto` kept -- also the theoretically preferred choice
  since it protects diversity).

**Library cleanup** (`implementation/lib/src/p3net/methods/p3net.py`):
removed the `cascade`, `truncation`, `stall_recovery`, `donor_pool`
dataclass fields, their `__post_init__` validation, and every branch in
`propose`/`update`/`_update_level_population`/`_sweep_proposals` that
dispatched on them -- the class now has exactly one behaviour along each
of these four axes instead of a runtime-selectable one. `analytic_cost`
stays a constructor arg (still legitimately `None`-able for
single-objective callers). `Pyramid.mark_stalled`
(`search_engines/p3/pyramid.py`) is also removed -- it existed solely to
support the now-gone `stall_recovery="grow"` path and had no other
caller; `Pyramid.promote`'s own stalling logic (the *default* pyramid-
growth trigger, unrelated to this ablation) is untouched. Removed 10
now-inapplicable unit tests across `lib/tests/test_p3net_pyramid_
integration.py` and `lib/tests/test_pyramid.py`, and rewrote one
(`test_is_stalled_reports_per_level_state`) to exercise `is_stalled` via
`promote()` instead of the deleted `mark_stalled`.

**Config cleanup**: deleted all nine `configs/methods/p3net_{analytic_
cost,cascade,f1_truncation,grow_on_stall,kappa_double,kappa_half,
threshold_permissive,threshold_strict,transient_donors}.yaml`. Removed
the now-inapplicable tests referencing them in
`experiments/tests/test_run_experiment.py` (nine tests) and
`experiments/tests/test_run_grid.py` (one test,
`test_enumerate_grid_excludes_sensitivity_ablation_arms_by_default` --
the `default_grid: false` mechanism itself stays, since it's still valid
generic infrastructure with no more p3net_* configs to demonstrate it on;
`reporting.MAIN_COMPARISON_METHODS` still independently guards the report
against the still-running `scripts/run_kappa_sensitivity.py`'s
`p3net_kappa_sensitivity__*` raw files).

**Data reconciliation**: `p3net_analytic_cost.yaml`'s already-collected
480 raw runs used identical seeds/budgets/search-spaces to `p3net.yaml`
on fully deterministic benchmarks, so they are exactly what a fresh run
of the new default would produce. Promoted them to `p3net__*.json`
(rewriting the `"method"` field inside each payload, not just the
filename) rather than re-running; the pre-decision `p3net__*.json` files
were archived, not deleted, at
`results/archive/p3net-pre-analytic-cost_2026-08-17/`. Verified: 480
matching (search_space, budget, seed) keys, no duplicates, no gaps;
`results/tables/fixed_budget_summary.md` regenerated from the reconciled
data still has exactly 176 rows across the eleven canonical arms, no
leaked method names. A full safety snapshot of the pre-cleanup state
(12180 raw files: main grid + all nine ablations + in-progress kappa
sweep) was taken first, at
`results/archive/R30_budgets-50-100-200-350_2026-08-17T111839_
pre-p3net-cleanup/`.

Both test suites green after this change (`implementation/lib`: 99
passed; `implementation/experiments`: 189 passed, 2 skipped).

### Added (report-level main-comparison filtering, 2026-08-16)

- `reporting/tables.py`: new `MAIN_COMPARISON_METHODS` constant -- the
  paper's eleven documented arms, explicit and fixed rather than derived.
  `scripts/generate_report.py::generate_report()` now filters loaded runs
  to this set before building any table or figure. Previously,
  `fixed_budget_summary_table`, `convergence_curve_figure`,
  `duplication_rate_figure`, etc. all derived their method sets *dynamically*
  from whatever `results/raw/*.json` files happened to be present -- safe
  only as long as `results/raw/` never held anything but the eleven
  documented arms. That assumption no longer holds now that the nine
  `p3net_*` sensitivity/design-choice ablation configs (`default_grid:
  false`) are meant to be run explicitly, sometimes into the same
  `results/raw/` folder as the main grid (e.g. one combined
  `--methods <11 arms> <9 ablations>` invocation). Filtering once at the
  `generate_report()` boundary, rather than patching every individual
  reporting function, keeps the paper's own report correct regardless of
  what else lives in `results/raw/`, while leaving `reporting/tables.py`
  and `reporting/plots.py` themselves generic (`tests/test_reporting.py`
  relies on that genericity with synthetic method names of its own, so
  the filter deliberately does not live inside those modules). Covered by
  `tests/test_generate_report.py` (new).

### Added (dataset-scope mitigation, 2026-08-16)

- `configs/search_spaces/jahs_bench_201_colorectal.yaml`,
  `jahs_bench_201_fashion.yaml` (new): JAHS-Bench-201 on its other two
  built-in datasets (`colorectal_histology`, `fashion_mnist`), identical to
  `jahs_bench_201.yaml` otherwise. Mitigates a limitation the R30 grid
  shares with the closest prior work (`bartnik2026evolutionary`, flagged in
  this project's own background research): both primary benchmarks
  evaluate a single dataset (NAS-HPO-Bench-II inherently so; JAHS-Bench-201
  only because its `dataset` field was left at the CIFAR-10 default, with
  no recorded reason to exclude the other two). `chapters/v003/conclusions/
  main.tex`'s Limitations/Future directions bullets updated to name this
  scope explicitly and point at these two files as the direct next step.
  **Not yet run.** Adding these files changes `scripts/run_grid.py`'s
  *default* (no `--search-spaces` given) grid from 2640 to 5280 points,
  since it auto-discovers every `configs/search_spaces/*.yaml` with no
  filtering mechanism (unlike methods' `not_yet_implemented`). This is a
  deliberate choice, confirmed 2026-08-16: the two new dataset variants
  are meant to be part of the *default* grid for the next experiment pass
  (all eleven documented arms x all four search spaces x all four budgets
  x R=30), not an opt-in add-on -- `tests/test_run_grid.py::
  test_enumerate_grid_defaults_to_every_config_file_on_disk` was updated
  to assert this explicitly (it previously asserted the opposite, a
  pre-decision placeholder that had gone stale and was failing).

### Fixed (sensitivity-ablation scope leak, 2026-08-16)

- `results/raw/`, `results/tables/`, `results/figures/` were reset to
  empty (`.gitkeep` only) ahead of a fresh grid run; the R10 and R30
  snapshots remain intact under `results/archive/`. In the course of
  checking readiness for that run, found that the nine `p3net_*`
  kappa/threshold/design-choice ablation configs added alongside
  `p3net.py`'s new `cascade`/`use_analytic_cost`/`truncation`/
  `stall_recovery`/`donor_pool` params (`p3net_analytic_cost.yaml`,
  `p3net_cascade.yaml`, `p3net_f1_truncation.yaml`,
  `p3net_grow_on_stall.yaml`, `p3net_kappa_double.yaml`,
  `p3net_kappa_half.yaml`, `p3net_threshold_permissive.yaml`,
  `p3net_threshold_strict.yaml`, `p3net_transient_donors.yaml`) had no
  default-grid exclusion, unlike `nsganetv2_continuous.yaml`'s
  `not_yet_implemented: true`. Since `reporting/tables.py`'s
  `fixed_budget_summary_table` derives its per-cell baseline set
  dynamically from whatever method names are present in `results/raw/`,
  running these nine alongside the eleven documented arms would have
  silently grown the Holm-Bonferroni comparison family from 10 to 19 per
  cell and broken the paper's "ten/eleven arms" framing throughout
  Findings -- with no existing test catching it, since the reporting
  tests use small synthetic fixtures rather than the real config
  directory. Fixed by adding a new `default_grid: false` key (distinct
  from `not_yet_implemented`, since these configs are fully runnable, just
  a separate analysis axis) to all nine configs and a matching filter in
  `scripts/run_grid.py::_runnable_method_names`; a new regression test
  (`test_enumerate_grid_excludes_sensitivity_ablation_arms_by_default`)
  covers it. These nine remain runnable individually via
  `scripts/run_experiment.py --method <name>` or explicit `--methods` on
  `run_grid.py`; the joint kappa x threshold sweep has its own dedicated,
  already-implemented and tested driver, `scripts/run_kappa_sensitivity.py`
  (`chapters/v003/results/main.tex`'s "Surrogate error accumulation"
  paragraph still describes this script as not implemented -- that text is
  now stale and needs updating once the sweep is actually run and
  reported).
- `chapters/v003/conclusions/main.tex` (Limitations bullet): corrected an
  overclaim that had crept in ahead of the actual run -- it stated the
  dataset-scope limitation "is since addressed by running the full grid,"
  past tense, while `results/raw/` had zero files for either new dataset.
  Reworded to "is mitigated, though not yet resolved as of this draft" and
  pointed at the archived $R{=}30$ CIFAR-10-only snapshot plus the pending
  next pass, so the text matches what has actually been run rather than
  what is merely configured.

### Added (results archiving, 2026-08-16)

- `scripts/archive_snapshot.py` (new): freezes `results/{raw,tables,figures}/`
  into one self-contained, identifiable `results/archive/<name>/` folder,
  with an auto-generated name (`auto_snapshot_name()`:
  `R{seeds}_budgets-{tiers}_{timestamp}`) if none is given, plus a
  `MANIFEST.md` template (file counts, git commit/dirty state pre-filled;
  headline result and known-gaps sections left as prompts). `results/raw/`
  is a live, additive database and `results/tables/`/`results/figures/` are
  point-in-time views `scripts/generate_report.py` overwrites on every run
  -- this exists so a later config change can't silently erase what an
  earlier analysis was based on.
- `scripts/generate_report.py` now calls `archive_snapshot()` automatically
  after every run by default (new `--archive-dir` and `--no-archive` CLI
  flags; `--no-archive` opts out for quick, throwaway iteration). The
  importable `generate_report()` function itself is unchanged and has no
  archiving side effect, so `tests/test_reporting.py`'s existing calls to it
  don't start creating archive folders.
- `results/archive/R10_budgets-50-100-200_2026-08-16/` and
  `R30_budgets-50-100-200-350_2026-08-16/` (the two hand-assembled snapshots
  from earlier today) retrofitted to the same self-contained shape: each now
  has its own `raw/` alongside `tables/`/`figures/`, rather than raw data
  living apart in a separate top-level `results/raw_archive/` folder. R10's
  `raw/` (540 files) is a reconstruction -- 480 files still unchanged in the
  live `results/raw/` (same method/search_space/budget/seed as the R10 run,
  never touched by the later R30 rerun) plus the 60 original `p3net` files
  recovered from `results/raw_archive/pre-surrogate-quality-diagnostic/`,
  verified byte-identical (`md5sum`) before that now-redundant folder was
  removed. R30's `raw/` is a straight copy of the live `results/raw/` at
  consolidation time. No experiments were rerun for this -- both snapshots'
  `tables/`/`figures/` numbers are unchanged, only where the backing raw
  data lives changed.

### Added

- Implemented the search space, substrates, NSGA-II,
  baseline/ablation methods, stopping rule + run driver, metrics/stats,
  all against a local synthetic/fake substrate since the real benchmark
  packages (jahs-bench, nashpobench2api) aren't installed yet — TDD
  throughout, 99 tests, `uv run ruff check .` clean.
- `search_spaces/nas_genotype.py` — six-edge NAS-Bench-201-style cell +
  discretised Θ shared by every arm (Fairness controls), plus a separate
  `ContinuousThetaBounds` representation for the `nsganetv2_continuous`
  control (not yet consumed — see Known gaps below).
- `substrates/{base,jahs_bench_201,nas_hpo_bench_ii}.py` — structural
  adapters; `query_f1`/`analytic_f2` raise `NotImplementedError` rather
  than a fake value until Stage C installs the real packages.
- `search_engines/nsga2/` — fast nondominated sort + crowding distance.
- `methods/{nsga_net,nsganetv2,p3_alone,p3_absolute,random_search}.py` +
  `methods/external/{sh_emoa,mo_bohb,tpe}.py` (ask/tell scaffolding over
  a shared `AskTellMethod`, real backends deferred to Stage C).
- `stopping_rules.py` — `ExplorationCollapse` + `BudgetOrExplorationCollapse`.
- `scripts/run_experiment.py` / `scripts/run_grid.py` — config-driven
  single-run and full-grid-sweep entry points, persisting H_t as JSON
  under `results/raw/`; `run_grid.py` skips points already on disk.
- `configs/methods/*.yaml`, `configs/search_spaces/*.yaml`,
  `configs/experiment/budgets.yaml` — real, non-placeholder config data.
- `metrics/{surrogate_quality,diagnostics}.py`,
  `stats/significance.py` — rank correlation / pairwise-comparison-accuracy
  surrogate quality, duplication rate / archive turnover diagnostics,
  paired Wilcoxon + Holm–Bonferroni + Cliff's delta over the defined
  P3Net-vs-nine-arms comparison set.

### Fixed

- `p3_absolute.py` and `p3_alone.py` each had a stall bug where a sweep
  producing only already-evaluated candidates would end the run early
  instead of injecting fresh random diversity (same class of bug already
  fixed in the library's `P3Net`); `p3_alone.py` additionally didn't check
  the dedup cache before returning a sweep proposal for real evaluation,
  undercounting unique evaluations. Both caught by real test runs, not
  inspection.
- `search_spaces/__init__.py` initially imported via a nonexistent
  `experiments.search_spaces.*` namespace; corrected to the flat
  `search_spaces.*` import every other module in this package uses
  (`experiments/pyproject.toml`'s wheel layout has no `experiments.`
  prefix).

### Changed (5-audit pass, 2026-08-14)

- Consolidated the rejection-sampling batch-generation loop, which had
  drifted into four near-identical copies (`p3_absolute._random_valid_batch`,
  `p3_alone._bootstrap_one`, `random_search.propose`, and the pre-existing
  `methods/_nsga2_shared.py::random_valid_batch`), into one shared
  `methods/_shared.py::random_valid_batch` used by all five arms.
  `methods/_nsga2_shared.py` renamed to `methods/_shared.py` since it's no
  longer NSGA-II-specific.
- Corrected `README.md` and `CONTRIBUTING.md`, which still claimed
  "scaffolding stage" / "every file holds a task list" despite Phases 1–6
  being fully implemented; added a runnable `## Usage` example to `README.md`.
- Added `docs/architecture/README.md` (C1 system-context diagram + module
  map), mirroring `../lib/docs/architecture/`.
- Added `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.md` and
  `.github/PULL_REQUEST_TEMPLATE.md`, present in `../lib/` but missing here.

### Added (Stage C, 2026-08-15)

- `search_spaces/nas_hpo_bench_ii_genotype.py` — NAS-HPO-Bench-II's own
  real search space (4 cell operations, not 5; `learning_rate` x
  `batch_size` only, not JAHS-Bench-201's 4-hyperparameter shape),
  verified against the real downloaded dataset rather than guessed —
  including an empirical determination of which cellcode digit is the
  null operation (querying `'3|33|333'` against the real data scores
  ~9.7% accuracy, chance level, confirming digit 3, not the usual
  NAS-Bench-201 convention of digit 0). `search_spaces/_cell_graph.py`
  factored out the six-edge DAG topology + path-existence check shared
  with `nas_genotype.py`, avoiding a second copy of that logic.
- `substrates/nas_hpo_bench_ii.py` now queries the real
  `NASHPOBench2API` against `data/cache/nashpobench2/` (dataset fetched
  via `gdown` from the Google Drive link in `nashpobench2api`'s own
  README) — no longer raises `NotImplementedError`. Verified end-to-end
  with a real `scripts/run_experiment.py` run.
- `methods/sh_emoa.py` — real (mu+lambda) EMOA implementation (uniform
  mutation/crossover, tournament selection, hypervolume-contribution
  survivor selection via `p3net.metrics.hypervolume`), replacing the old
  `methods/external/sh_emoa.py` ask/tell stub. No published SH-EMOA
  package exists to wrap; verified by reading
  `automl/multi-obj-baselines` (the paper's own reference code) directly.
- Installed `optuna`, `nashpobench2api`, and `hpbandster` (the latter via
  a local `netifaces` stub package, `vendor/netifaces-stub/` — the real
  `netifaces` has no prebuilt wheel for modern Python on Windows and is
  only ever touched by hpbandster's distributed-worker nameserver, which
  this project's ask/tell usage never starts).
- `substrates/jahs_bench_201.py` now queries real JAHS-Bench-201 data,
  via a subprocess bridge to `vendor/jahsbench-env/` (a dedicated Python
  3.10 environment — jahs-bench cannot install in this project's main
  Python 3.13 environment at all, see Known gaps in the previous entry,
  now resolved). `vendor/jahsbench-env/query_server.py` is a
  **persistent** bridge process (JSON-lines over stdin/stdout), not one
  spawned per query, since loading the surrogate models takes several
  minutes. Surrogate data (~1.65GB) downloaded to `data/cache/
  jahs_bench_201/` (gitignored) via `curl` with resume support, after
  the package's own downloader (no retry, buffers the whole file in
  memory) failed twice on transient connection drops.
  `search_spaces/nas_genotype.py` needed no changes — its assumed search
  space was verified correct against the real `jahs_bench.lib.core.
  configspace` module, unlike NAS-HPO-Bench-II's.
- `methods/external/tpe.py` now wraps real `optuna.samplers.TPESampler`
  via optuna's ask/tell API. Every optuna trial is eventually told
  something real (FAILED for invalid genotypes, the real cached value
  for duplicates, or the real evaluation result) rather than left
  permanently un-told, which would leak optuna-internal state.
- `methods/external/mo_bohb.py` now wraps the real, pip-installed
  `hpbandster.optimizers.config_generators.bohb.BOHB` config generator.
  The paper's actual MO-BOHB depends on a custom, unpublished fork of
  hpbandster (`automl/multi-obj-baselines`'s own vendored copy) not
  available via `pip install hpbandster` — this is a documented
  adaptation: real BOHB, single-objective by construction, driven with
  random-weight Tchebycheff scalarisation of `(f1, f2)` into the one
  loss it needs (the same technique visible, unwired, in the reference
  implementation's own `MOBOHBWorker.tchebycheff_norm`). Resolves the
  fidelity-ladder-usage open decision concretely: always queries at r_K
  (fixed budget), the same harness-level limitation already documented
  for `methods/sh_emoa.py`'s missing successive-halving half.
- `methods/external/_ask_tell_shared.py`'s `default_valid_sampler`
  removed — no callers left once SH-EMOA/MO-BOHB/TPE were all wired to
  real backends.

### Added (Phase 7 reporting, 2026-08-15)

- `reporting/{_common,tables,plots,__init__}.py` — turns `results/raw/*.json`
  into the paper's Results-section artifacts: `fixed_budget_summary_table`
  (median/IQR, IGD+ or best-known-front-relative hypervolume, Holm-corrected
  significance + Cliff's delta vs. P3Net over exactly the defined comparison
  set), `p3_alone_sweep_completion_table` (the "Baselines" paragraph's
  sweeps-completed side table), and `convergence_curve_figure`/
  `pareto_front_progression_figure`/`sensitivity_figure`/
  `duplication_rate_figure` (each returns a `matplotlib.figure.Figure`,
  file-writing left to the caller). `matplotlib` added as an optional
  `reporting` extra (`pyproject.toml`), not a base dependency.
- `scripts/generate_report.py` — loads every raw run, writes the tables to
  `results/tables/*.md` and the figures to `results/figures/*.png`, in the
  paper's promised reporting order; skips the kappa/threshold sensitivity
  step with an explicit note (its data source, `run_kappa_sensitivity.py`,
  isn't implemented yet) rather than silently omitting it.
- `tests/test_reporting.py` — 23 tests: synthetic-data smoke checks for
  every table/plot function (per the implementation plan's own note that
  these aren't unit-tested against one checkable value, since they render
  output), a `persist_run`/`load_raw_run` round-trip test, and a real
  end-to-end `generate_report()` run.
- `.github/workflows/ci.yml` now syncs `--extra reporting` alongside
  `--extra dev`, since `tests/test_reporting.py` imports `matplotlib`.

### Changed

- `scripts/run_experiment.py`'s `run_single` now returns a `RunResult`
  (state + cache + method) instead of a bare `RunState`, so `persist_run`
  can capture per-run diagnostics (`duplication_rate`; `sweeps_completed`
  for `p3_alone`) that `reporting/tables.py`'s sweep-completion table
  needs — an additive JSON field (`"diagnostics"`), older raw files without
  it still load correctly (`reporting._common.load_raw_run` defaults it to
  `{}`). Ripple-updated `run_grid.py` and the 4 `run_single`/`persist_run`
  call sites in `tests/test_run_experiment.py`.
- `configs/methods/p3net.yaml` and a `test_run_experiment.py` test:
  `population_size` replaced with `growth_factor`, following the library's
  `P3Net` dropping `population_size` as a constructor argument entirely
  in favour of a self-growing population pyramid.

### Fixed (Holm-Bonferroni correction scope, 2026-08-16)

- `reporting/tables.py`'s `fixed_budget_summary_table` was pooling every
  P3Net-vs-baseline comparison across *every* `(search_space, budget)` cell
  into one list before calling `compare_p3net_to_baselines` once, inflating
  the Holm-Bonferroni correction family from the 8 comparisons the
  Statistical plan defines ("P3Net against each of the other nine arms...
  per benchmark and per budget tier") to as many as 48 when the function is
  called on the full run set, as `scripts/generate_report.py` does. This
  silently over-corrected every adjusted $p$-value. Fixed by correcting each
  `(search_space, budget)` cell's comparisons in their own
  `compare_p3net_to_baselines` call, merging the per-cell results afterwards.
  Regenerating `results/tables/fixed_budget_summary.md` on the existing raw
  runs flips 7 of 48 comparisons from "no" to "yes" (Reject H0): SH-EMOA and
  TPE vs. P3Net at JAHS-Bench-201 budget 100 and 200; NSGA-Net vs. P3Net and
  P3-alone vs. P3Net (P3Net ahead here, $\delta=+0.8$) at JAHS-Bench-201
  budget 200; NSGANetV2 vs. P3Net at NAS-HPO-Bench-II budget 200.
  `tests/test_reporting.py::test_fixed_budget_summary_table_scopes_holm_correction_per_cell`
  added as a regression test (two cells, one with a completely-separated
  6-seed comparison that is significant alone but would be erased if pooled
  with an unrelated null cell's comparisons).

### Added (live surrogate-quality logging, 2026-08-16)

- `p3net.methods.p3net.P3Net` (library) now records `surrogate_quality_log`
  (a list of `(|H_t| at scoring time, predicted delta, true delta)`) for
  every proposal a fitted $\hat{\delta}_F$ actually scored and that was
  later really evaluated — a live signal, not a post-hoc refit, since the
  surrogate is retrained every sweep on whatever $\mathcal{H}_t$ existed
  then and a refit on the final persisted history cannot reproduce that.
  Bootstrap-phase and stall/diversity-injection proposals (no surrogate
  involved) are correctly excluded. `scripts/run_experiment.py`'s
  `_diagnostics` persists it (additive, only present for `p3net` runs);
  `reporting.surrogate_quality_figure` (new) bins the pooled log by
  `|H_t|` and plots `metrics.surrogate_quality.pairwise_comparison_accuracy`
  per bin (the relative-surrogate-appropriate metric — rank correlation
  doesn't apply to a surrogate that never predicts an absolute value);
  wired into `scripts/generate_report.py` as
  `results/figures/surrogate_quality__p3net.png`, skipped (no file written)
  if no loaded run carries the new diagnostic. None of the existing 540 raw
  runs do — they predate this capability — so a rerun of the `p3net` arm is
  needed to actually populate the figure.
- `tests/test_reporting.py`: 3 new tests for `surrogate_quality_figure`
  (no-data guard, per-bin sign-agreement scoring, other-method filtering).
  Existing `p3net` library integration tests (16, `implementation/lib`)
  still pass unchanged.

### Changed (experiment grid expansion, 2026-08-16)

- `configs/experiment/budgets.yaml`: `seeds` 1-10 (R=10) → 1-30 (R=30);
  `budget_tiers` gains 350 (still ≤ NSGANetV2's own 350-evaluation
  convention, "Budgets, seeds, stopping"). Motivated by the archived
  R=10/{50,100,200} snapshot's power analysis: several comparisons carried
  a large Cliff's delta without significance, and budget=50 had zero
  significant comparisons on either benchmark despite visibly tight
  convergence-plot clustering.
- `configs/methods/p3_alone_pop20.yaml`, `p3_alone_pop40.yaml` (new):
  `p3_alone` (same class) at `population_size` 20 (matching every external
  baseline's own 20 — `p3_alone.yaml`'s original 10 was the one arm running
  half its peers' population) and 40, to isolate whether P3-alone's
  diagnostics (highest duplication rate and sweep count, lowest-or-near-
  lowest hypervolume-relative median in the grid) reflect "no surrogate" or
  the unexamined smaller-population confound.
- `results/raw/p3net__*.json` (60 files, the original R=10/{50,100,200}
  grid) moved to `results/raw_archive/pre-surrogate-quality-diagnostic/`
  so `scripts/run_grid.py` treats those points as not-yet-run and
  regenerates them under the current `P3Net`, which now logs
  `surrogate_quality_log`. A plain `run_grid.py` invocation (no flags) now
  covers the full expanded plan in one pass: 11 runnable methods × 2
  search spaces × 4 budgets × 30 seeds = 2640 grid points, of which 480 are
  already cached (every non-`p3net` point from the original R=10 grid, at
  seeds 1-10, budgets 50/100/200) and 2160 will actually run.

### Known gaps (tracked, not silently dropped)

- `methods/nsganetv2.py` only implements the shared discretised-Θ variant;
  the `nsganetv2_continuous` control needs a real-valued crossover
  operator this class doesn't have yet.
- `scripts/run_kappa_sensitivity.py` is not implemented yet;
  `reporting/plots.py`'s `sensitivity_figure` is ready to consume its
  output once it exists.
- `reporting/plots.py` has no archive-turnover plot: it needs
  per-generation population snapshots `scripts/run_experiment.py` doesn't
  persist (only the final H_t is written) — a harness-level gap.
- `methods/sh_emoa.py` and `methods/external/mo_bohb.py` each implement
  only the fixed-fidelity (r_K) half of their real algorithms; the
  successive-halving/multi-fidelity half needs harness-level support for
  querying below r_K, which doesn't exist yet (`p3net.harness.Runner` /
  `substrates.Substrate`).
- JAHS-Bench-201 live-query tests (`tests/test_substrates.py`) are
  opt-in (`RUN_JAHS_BENCH_LIVE_TESTS=1`) since starting the bridge takes
  several minutes just to load the surrogate models — not run by
  default `uv run pytest`.
