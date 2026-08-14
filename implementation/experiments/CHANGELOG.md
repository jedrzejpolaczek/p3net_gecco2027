# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to the phase-based scaffolding described in
[`TASKS.md`](TASKS.md) rather than strict [Semantic Versioning](https://semver.org/)
until a first `0.1.0` release is reached.

## [Unreleased]

### Added

- Implemented `TASKS.md` Phases 1–6 (search space, substrates, NSGA-II,
  baseline/ablation methods, stopping rule + run driver, metrics/stats),
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

### Known gaps (tracked in `TASKS.md`, not silently dropped)

- `methods/nsganetv2.py` only implements the shared discretised-Θ variant;
  the `nsganetv2_continuous` control needs a real-valued crossover
  operator this class doesn't have yet.
- `scripts/run_kappa_sensitivity.py` and `reporting/*` (Phase 7) are not
  implemented — deferred past this Stage B pass.
- `methods/external/*` wrap a Stage-B stand-in sampler; the real
  pymoo/Optuna/HpBandSter backends, and MO-BOHB's fidelity-ladder usage,
  are Stage C decisions.
