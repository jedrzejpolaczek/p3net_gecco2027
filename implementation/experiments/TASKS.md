# Experiments task index (GECCO 2027 paper reproduction)

Phases 1–6 are implemented (real code, TDD, `uv run pytest` all green,
`uv run ruff check .` clean) — see each phase below for what's real vs.
still deferred to Stage C. This assumes the `p3net` library
([`../lib/TASKS.md`](../lib/TASKS.md)) is already implemented and installed
here as a local editable dependency on `../lib` (`experiments/pyproject.toml`)
— every phase below imports it as `p3net.*`, never via a relative path into
`../lib/src/p3net`.

## Phase 0 — Environment & scaffolding

- [x] Repo scaffolding — `README.md`, `LICENSE` (AGPLv3), `CODE_OF_CONDUCT.md`,
      `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `.gitattributes`,
      `.gitignore`, `.github/workflows/ci.yml`, `.github/dependabot.yml`
- [x] [`pyproject.toml`](pyproject.toml) — manifest scaffolded, incl. the
      local editable `p3net` dependency (`[tool.uv.sources]`); `pyyaml`
      (config loading) and `scikit-learn` (surrogate model family, used
      directly by `scripts/run_experiment.py` and several tests) added as
      Phases 5–6 landed. Real benchmark/baseline deps (jahs-bench,
      nashpobench2api, pymoo, optuna, hpbandster) still not added — Stage C

## Phase 1 — Concrete NAS search space ✅ implemented

Implements the library's generic `p3net.problem` interfaces for this
paper's domain. Nothing benchmark- or method-specific can be written before
this exists.

- [x] [`search_spaces/nas_genotype.py`](search_spaces/nas_genotype.py) — six architecture edges + discretised Θ, plus the continuous-Θ control variant (structural definition; "unverified against live data" per its own docstring)
- [x] [`search_spaces/__init__.py`](search_spaces/__init__.py)
- [x] [`tests/test_nas_search_space.py`](tests/test_nas_search_space.py)

## Phase 2 — Benchmark substrates ✅ implemented (structural)

Depend on `search_spaces/` for the concrete genotype they translate to/from
each benchmark's own query format.

- [x] [`substrates/base.py`](substrates/base.py) — common query interface, fidelity ladder exposure
- [x] [`substrates/jahs_bench_201.py`](substrates/jahs_bench_201.py) — Category 2 adapter; `query_f1`/`analytic_f2` raise `NotImplementedError` until Stage C (jahs-bench not installed) — deliberately not stubbed with fake data
- [x] [`substrates/nas_hpo_bench_ii.py`](substrates/nas_hpo_bench_ii.py) — Category 1 adapter; same `NotImplementedError` policy, plus a real `ValueError` guard rejecting any fidelity beyond `MAX_TABULATED_EPOCHS`
- [x] [`substrates/__init__.py`](substrates/__init__.py)
- [x] [`tests/test_substrates.py`](tests/test_substrates.py)
- [x] [`configs/search_spaces/jahs_bench_201.yaml`](configs/search_spaces/jahs_bench_201.yaml)
- [x] [`configs/search_spaces/nas_hpo_bench_ii.yaml`](configs/search_spaces/nas_hpo_bench_ii.yaml)

## Phase 3 — NSGA-II (needed only for baselines) ✅ implemented

Depends on `search_spaces/` (genotype). Independent of Phase 2, can be built
in parallel with it.

- [x] [`search_engines/nsga2/nondominated_sort.py`](search_engines/nsga2/nondominated_sort.py)
- [x] [`search_engines/nsga2/crowding_distance.py`](search_engines/nsga2/crowding_distance.py)
- [x] [`search_engines/nsga2/__init__.py`](search_engines/nsga2/__init__.py)
- [x] [`search_engines/__init__.py`](search_engines/__init__.py)
- [x] [`tests/test_nsga2.py`](tests/test_nsga2.py) — gap in the original task list, added

## Phase 4 — Baseline/ablation methods ✅ implemented

Each depends on `p3net.search_engines.p3` / `p3net.surrogates.*` (library,
already implemented) or `experiments.search_engines.nsga2` (Phase 3), plus
`substrates/` (Phase 2) as the objective source. Ordered simplest-first.

- [x] [`methods/nsga_net.py`](methods/nsga_net.py) — NSGA-II, no surrogate
- [x] [`methods/p3_alone.py`](methods/p3_alone.py) — P3 (library), no surrogate, real-eval-gated sweep; `sweeps_completed` diagnostic
- [x] [`methods/nsganetv2.py`](methods/nsganetv2.py) — NSGA-II + absolute regressor, shared discretised Θ. **Known gap**: the continuous-Θ control variant is NOT implemented (needs a parallel real-valued crossover operator this class doesn't have) — `configs/methods/nsganetv2_continuous.yaml` is marked `not_yet_implemented: true` and `scripts/run_experiment.py::build_method` raises `NotImplementedError` for it rather than silently running the wrong thing
- [x] [`methods/p3_absolute.py`](methods/p3_absolute.py) — P3 (library) + absolute regressor
- [x] [`methods/random_search.py`](methods/random_search.py) — own implementation, not a wrapper (too simple to carry reimplementation risk)
- [x] [`methods/external/tpe.py`](methods/external/tpe.py) — ask/tell scaffolding; real Optuna backend deferred to Stage C
- [x] [`methods/external/sh_emoa.py`](methods/external/sh_emoa.py) — ask/tell scaffolding; real pymoo backend deferred to Stage C
- [x] [`methods/external/mo_bohb.py`](methods/external/mo_bohb.py) — ask/tell scaffolding; real HpBandSter/Optuna backend AND the fidelity-ladder-usage decision both deferred to Stage C
- [x] [`methods/external/_ask_tell_shared.py`](methods/external/_ask_tell_shared.py) — shared `AskTellMethod` + `default_valid_sampler` (not in the original task list, added to avoid reimplementing the same ask/tell loop three times)
- [x] [`methods/external/__init__.py`](methods/external/__init__.py)
- [x] [`methods/_shared.py`](methods/_shared.py) — shared rejection-sampling batch generation (used by every arm) + NSGA-II crossover/mutation/survivor-selection helpers (used by `nsga_net.py`/`nsganetv2.py`); not in the original task list, added proactively and then consolidated further during the 5-audit pass (2026-08-14) after the maintainability audit caught the same batch-generation loop duplicated across `p3_absolute.py`/`p3_alone.py`/`random_search.py`
- [x] [`methods/__init__.py`](methods/__init__.py)
- [x] [`configs/methods/*.yaml`](configs/methods/) — all ten (incl. `p3net.yaml`, which configures the library's `p3net.methods.p3net` directly); `model_factory` (a Python callable) is supplied by `scripts/run_experiment.py`, not stored in YAML
- [x] [`tests/test_methods.py`](tests/test_methods.py), [`tests/test_external_wrappers.py`](tests/test_external_wrappers.py) — gaps in the original task list, added

## Phase 5 — Stopping rule + run driver + experiment configs ✅ implemented

`stopping_rules.py` implements `p3net.harness.runner`'s `StoppingRule`
protocol (library, already implemented). Depends on Phases 1–4 all being in
place, since the driver runs an arbitrary method against an arbitrary
substrate.

- [x] [`stopping_rules.py`](stopping_rules.py) — `ExplorationCollapse` + `BudgetOrExplorationCollapse` composing it with the library's default budget-exhaustion rule
- [x] [`configs/experiment/budgets.yaml`](configs/experiment/budgets.yaml) — tiers {50,100,200}, R=10 seeds, stopping-rule params
- [x] [`configs/experiment/kappa_threshold_sweep.yaml`](configs/experiment/kappa_threshold_sweep.yaml) — grid data only; **not yet consumed** (see `run_kappa_sensitivity.py` below)
- [x] [`scripts/run_experiment.py`](scripts/run_experiment.py) — single run entry point: loads a method/search-space config, builds the method+substrate via small registries (`_SEARCH_SPACE_BUILDERS`, `_SUBSTRATE_BUILDERS`, `_ASK_TELL_FACTORIES`), runs it through `p3net.harness.Runner`, persists H_t as JSON under `results/raw/`. CLI-smoke-tested against a real (Stage-C-gated) config: fails loudly with the substrate's own `NotImplementedError`, exactly as designed
- [x] [`scripts/run_grid.py`](scripts/run_grid.py) — full ablation-grid sweep: `enumerate_grid` (full cross product of methods × search spaces × budgets × seeds) + `run_grid` (dispatches each point in-process, skips points already persisted under `results/raw/` unless `--no-skip-cached`)
- [x] [`tests/test_stopping_rules.py`](tests/test_stopping_rules.py), [`tests/test_run_experiment.py`](tests/test_run_experiment.py), [`tests/test_run_grid.py`](tests/test_run_grid.py) — gaps in the original task list, added (all three run against a fake in-repo `Substrate`, since the real substrates raise `NotImplementedError` until Stage C)
- [ ] [`scripts/run_kappa_sensitivity.py`](scripts/run_kappa_sensitivity.py) — **not implemented**: reports surrogate rank correlation via `metrics/surrogate_quality.py`, which now exists (Phase 6, below) but this script itself is deferred — out of scope for the plan's Stage B (which named only `run_experiment.py`/`run_grid.py` explicitly)

## Phase 6 — Metrics & statistics ✅ implemented

Consume the H_t / run records produced by Phase 5.

- [x] [`metrics/surrogate_quality.py`](metrics/surrogate_quality.py) — `rank_correlation` (Spearman/Kendall, for absolute-value surrogates), `pairwise_comparison_accuracy` (sign-agreement, for the relative δ̂_F surrogate, which has no absolute prediction to rank-correlate), `surrogate_quality_trace` (rank correlation as a function of |H_t| by refitting on growing prefixes)
- [x] [`metrics/diagnostics.py`](metrics/diagnostics.py) — `duplication_rate` (thin re-export of `EvaluationCache.duplication_rate`, kept as a single source of truth rather than a second counting mechanism), `archive_turnover` (entries/exits between consecutive archive snapshots)
- [x] [`metrics/__init__.py`](metrics/__init__.py)
- [x] [`tests/test_experiment_metrics.py`](tests/test_experiment_metrics.py)
- [x] [`stats/significance.py`](stats/significance.py) — `compare_p3net_to_baselines` (paired Wilcoxon signed-rank over exactly the given `Comparison` list, never all pairwise combinations), `holm_bonferroni_correction` (standard Holm step-down, matches R's `p.adjust(method="holm")`), `cliffs_delta` (effect size, reported for every comparison)
- [x] [`stats/__init__.py`](stats/__init__.py)
- [x] [`tests/test_significance.py`](tests/test_significance.py) — gap in the original task list, added

## Phase 7 — Reporting

Depends on `metrics/`, `stats/` (Phase 6), and `p3net.metrics` (library,
already implemented).

- [ ] [`reporting/tables.py`](reporting/tables.py) — fixed-budget summary table
- [ ] [`reporting/plots.py`](reporting/plots.py) — convergence, Pareto progression, sensitivity, diagnostics, best-known-front construction
- [ ] [`reporting/__init__.py`](reporting/__init__.py)
- [ ] [`scripts/generate_report.py`](scripts/generate_report.py) — produces the Results-section artifacts, in the paper's promised order

## Open decisions carried into the task list

1. **Best-known-front definition** (`reporting/plots.py`, feeding
   `p3net.metrics.hypervolume`) — candidate is "union of all points
   evaluated by any compared method across all runs"; paper flags this as
   open.
2. **MO-BOHB's fidelity-ladder usage** (`methods/external/mo_bohb.py`) —
   Hyperband is naturally fidelity-aware; whether/how it consumes
   `p3net.problem`'s generic fidelity ladder needs an explicit decision.
