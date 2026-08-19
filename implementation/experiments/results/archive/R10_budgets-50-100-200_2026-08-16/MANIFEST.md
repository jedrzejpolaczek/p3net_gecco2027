# Archived report snapshot: R10_budgets-50-100-200_2026-08-16

Self-contained frozen copy of `raw/`, `tables/`, and `figures/` at the point
described below, so a later report regeneration (more seeds, more budgets,
different method configs) doesn't silently overwrite the numbers this
snapshot's analysis and this project's history are based on.

`raw/` here (540 files) is a **reconstruction**, assembled 2026-08-16 (after
the R30 rerun) from two sources that together reproduce exactly what
`results/raw/` contained when this snapshot's `tables/`/`figures/` were
generated: (1) the 480 non-`p3net` files at seeds 1-10 and budgets
{50,100,200}, still present unchanged in the live `results/raw/` today since
no later run ever touched that exact (method, search_space, budget, seed)
combination, and (2) the 60 original `p3net` files at those same points,
which the live `results/raw/` no longer has (they were superseded when the
R30 rerun regenerated `p3net` with the new `surrogate_quality_log`
diagnostic) — recovered from what was, until this consolidation, a separate
top-level `results/raw_archive/pre-surrogate-quality-diagnostic/` folder,
now folded in here instead of living apart from the rest of this snapshot.
Verified byte-identical (`md5sum`) to that folder's content before it was
removed.

## Experiment configuration

- `configs/experiment/budgets.yaml`: `budget_tiers: [50, 100, 200]`,
  `seeds: [1..10]` (R=10).
- `configs/methods/*.yaml`: the 9-arm grid as of this date — `mo_bohb`,
  `nsga_net`, `nsganetv2`, `p3_absolute` (`population_size: 20`), `p3_alone`
  (`population_size: 10`), `p3net` (`growth_factor: 2`, `kappa: null` →
  default $2\lceil\log_2 n\rceil$, `acceptance_threshold: 0.0`),
  `random_search`, `sh_emoa`, `tpe`. `nsganetv2_continuous` excluded
  (`not_yet_implemented: true`).
- `configs/search_spaces/*.yaml`: `jahs_bench_201`, `nas_hpo_bench_ii`.
- 540 raw runs total (9 methods × 2 search spaces × 3 budgets × 10 seeds).

## Code state

- Base commit: `1a0c0e3` ("docs: modular C4 architecture docs; drop TASKS.md
  and ADR process logs"), plus one **uncommitted** working-tree fix present
  when this snapshot was generated:
  `reporting/tables.py`'s `fixed_budget_summary_table` now scopes the
  Holm-Bonferroni correction to each `(search_space, budget)` cell
  independently (8 comparisons), instead of pooling all 6 cells into one
  48-comparison family before correcting. **This snapshot is POST-fix** — the
  `Adj. p` / `Reject H0` values here differ from an earlier, buggy report
  generation (7 of 48 comparisons flip from "no" to "yes" under the fix; see
  `CHANGELOG.md`, "Fixed (Holm-Bonferroni correction scope, 2026-08-16)").
- Regenerated via `PYTHONPATH="../lib/src:." python3 scripts/generate_report.py`.

## Known gaps at this snapshot (see `chapters/v003/results/main.tex`, Findings)

- Surrogate quality (rank correlation vs. $|\mathcal{H}_t|$): not available —
  `metrics/surrogate_quality.py` did not exist yet at this snapshot.
- $\kappa$/acceptance-threshold sensitivity: not available —
  `scripts/run_kappa_sensitivity.py` not implemented yet.
- IGD+ for NAS-HPO-Bench-II: planned (its lookup table admits an exact
  oracle front) but not wired into this run — both benchmarks report
  hypervolume-relative-to-pooled-best-known-front instead.

## Headline result at this snapshot

7 of 48 P3Net-vs-baseline comparisons reject $H_0$ at $\alpha=0.05$: P3Net
significantly beats P3-alone at JAHS-Bench-201 budget 200 ($\delta=+0.80$);
SH-EMOA, TPE beat P3Net at JAHS budget 100 and 200; NSGA-Net beats P3Net at
JAHS budget 200; NSGANetV2 beats P3Net at NAS-HPO-Bench-II budget 200. Every
comparison at budget 50, on both benchmarks, is non-significant. Full numbers
in `tables/fixed_budget_summary.md`.

## Raw-data collision warning

`results/raw/*.json` is named `{method}__{search_space}__budget{budget}__seed{seed}.json`
— it does **not** encode method *hyperparameters* (e.g. `population_size`).
Re-running an existing method name at an existing (search_space, budget,
seed) point with a **changed config** (e.g. `p3_alone` with
`population_size: 30` instead of `10`) will silently overwrite the raw file
this snapshot's `p3_alone` numbers were computed from. Any follow-up
experiment that changes a method's hyperparameters must use either a new
method name (e.g. a new `configs/methods/p3_alone_pop30.yaml` with
`method: p3_alone_pop30` wired to the same class) or a separate
`--raw-results-dir`, not the existing method name in place.
