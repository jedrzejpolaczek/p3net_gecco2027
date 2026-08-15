# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project does not yet follow strict [Semantic Versioning](https://semver.org/)
until a first `0.1.0` release is reached.

## [Unreleased]

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
