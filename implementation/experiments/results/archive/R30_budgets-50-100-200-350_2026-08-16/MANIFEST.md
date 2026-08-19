# Archived report snapshot: R30_budgets-50-100-200-350_2026-08-16

Self-contained frozen copy of `raw/` (2640 files, exact copy of live
`results/raw/` at archival time), `tables/`, and `figures/`, superseding
`R10_budgets-50-100-200_2026-08-16` (still kept, not overwritten, and now
also self-contained — see its own MANIFEST). Backs this date's rewrite of
`chapters/v003/results/main.tex`'s Findings. This is currently the
**live/current** experiment state as well: `results/raw/` keeps growing as
new grid points are added, so this snapshot's `raw/` will silently fall
behind the live one over time -- re-copy at the next archival point if an
exact record is needed again, rather than assuming this folder tracks it
automatically.

## Experiment configuration

- `configs/experiment/budgets.yaml`: `budget_tiers: [50, 100, 200, 350]`,
  `seeds: [1..30]` (R=30) — extended from the R10 snapshot's `{50,100,200}`/
  R=10 following that snapshot's own power analysis (large-|delta|,
  non-significant comparisons; budget=50 uniformly non-significant despite
  tight convergence-plot clustering).
- `configs/methods/*.yaml`: the original 9-arm grid plus two new arms,
  `p3_alone_pop20` (population_size 20, matching every other baseline) and
  `p3_alone_pop40` (population_size 40) — isolates the population-size
  confound `p3_alone.yaml`'s original `population_size: 10` carried
  unexamined (smaller than every other arm in the grid).
- `configs/search_spaces/*.yaml`: `jahs_bench_201`, `nas_hpo_bench_ii`.
- 2640 raw runs total (11 methods × 2 search spaces × 4 budgets × 30 seeds).
  `p3net`'s 60 original R10/seeds-1-10 raw files were moved aside before this
  run (later consolidated into `R10_budgets-50-100-200_2026-08-16/raw/`, see
  that snapshot's own MANIFEST) so every `p3net` raw file here, including
  seeds 1-10, carries `surrogate_quality_log`.

## Code state

Same as `R10_budgets-50-100-200_2026-08-16`'s MANIFEST (per-cell
Holm-Bonferroni scoping fix, live surrogate-quality logging) — no further
code changes between that snapshot and this one, only the config expansion
above and the resulting rerun.

## Headline result at this snapshot

34 of 80 P3Net-vs-baseline comparisons reject $H_0$ at $\alpha=0.05$ (up
from 7 of 48 at R=10): 7 favour P3Net (mostly P3-alone and P3-alone-pop20 at
JAHS-Bench-201, i.e. the core "surrogate helps" ablation; one exception,
MO-BOHB, at NAS-HPO-Bench-II budget 350), 27 favour the baseline —
concentrated at budget $\geq$ 100 against SH-EMOA, TPE, NSGA-Net, NSGANetV2,
and P3+absolute-regressor, on both benchmarks, growing more numerous as
budget grows. Budget 50 remains the tier where P3Net looks best relative to
the field (rank 9/11 by median on JAHS, i.e. 3rd-highest) but that reverses
by budget 100 (rank 5/11, roughly median) and stays there or worse through
budget 350. On NAS-HPO-Bench-II P3Net's median is never above the middle of
the field at any budget, and is last or second-last at budgets 50 and 350.
Full numbers in `tables/fixed_budget_summary.md`.

## Known gaps unchanged from the R10 snapshot

- $\kappa$/acceptance-threshold sensitivity: still not available
  (`scripts/run_kappa_sensitivity.py` not implemented).
- IGD+ for NAS-HPO-Bench-II: still not wired into this run; both benchmarks
  report hypervolume-relative-to-pooled-best-known-front.

## Newly available at this snapshot

- Surrogate quality: `figures/surrogate_quality__p3net.png` now has real
  data (all `p3net` raw files carry `surrogate_quality_log`). Pairwise
  comparison accuracy sits consistently around 0.62-0.75 across the
  observed $|\mathcal{H}_t|$ range (976 down to 100-330 points per bin, bin
  count shrinks as fewer runs reach very large history sizes), well above
  the 0.5 chance line throughout, with no clear degradation trend.
- Population-size ablation: `p3_alone_pop20`/`p3_alone_pop40` rows in
  `tables/fixed_budget_summary.md` and their bars in
  `figures/duplication_rate.png`.
