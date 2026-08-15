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
      Phases 5–6 landed. Stage C added `optuna`, `nashpobench2api`,
      `hpbandster` (+ its real deps `Pyro4`/`serpent`/`ConfigSpace`/
      `statsmodels`, + a local `netifaces` stub — see Stage C below);
      `pymoo` was added then removed once real SH-EMOA turned out not to
      need it. `jahs-bench` could not be added to this environment at all
      (see Stage C).

## Phase 1 — Concrete NAS search space ✅ implemented

Implements the library's generic `p3net.problem` interfaces for this
paper's domain. Nothing benchmark- or method-specific can be written before
this exists.

- [x] [`search_spaces/nas_genotype.py`](search_spaces/nas_genotype.py) — six architecture edges + discretised Θ, plus the continuous-Θ control variant; targets JAHS-Bench-201 specifically (structural definition; "unverified against live data" per its own docstring — jahs-bench still can't install, so this remains unverified)
- [x] [`search_spaces/nas_hpo_bench_ii_genotype.py`](search_spaces/nas_hpo_bench_ii_genotype.py) — **added in Stage C**: NAS-HPO-Bench-II's own real search space (4 ops, not 5; `learning_rate` x `batch_size` only, not the 4-hyperparameter JAHS-Bench-201 shape). Verified against the real downloaded dataset, including an empirical determination of which cellcode digit is the null operation (see its module docstring) — not guessed from documentation
- [x] [`search_spaces/_cell_graph.py`](search_spaces/_cell_graph.py) — **added in Stage C**: the six-edge DAG topology + input-output path check shared by both genotype modules, factored out to avoid duplicating it a second time (the same class of fix as `methods/_shared.py`)
- [x] [`search_spaces/__init__.py`](search_spaces/__init__.py)
- [x] [`tests/test_nas_search_space.py`](tests/test_nas_search_space.py)
- [x] [`tests/test_nas_hpo_bench_ii_genotype.py`](tests/test_nas_hpo_bench_ii_genotype.py) — **added in Stage C**, includes a real-data cross-check (skipped automatically if the dataset isn't downloaded)

## Phase 2 — Benchmark substrates ✅ implemented (structural)

Depend on `search_spaces/` for the concrete genotype they translate to/from
each benchmark's own query format.

- [x] [`substrates/base.py`](substrates/base.py) — common query interface, fidelity ladder exposure
- [x] [`substrates/jahs_bench_201.py`](substrates/jahs_bench_201.py) — Category 2 adapter; `query_f1`/`analytic_f2` still raise `NotImplementedError` — jahs-bench cannot install in this project's main environment (Stage C below) — deliberately not stubbed with fake data
- [x] [`substrates/nas_hpo_bench_ii.py`](substrates/nas_hpo_bench_ii.py) — Category 1 adapter — **real as of Stage C**: queries the live downloaded dataset via `nashpobench2api`, using `search_spaces/nas_hpo_bench_ii_genotype.py` (not `nas_genotype.py`). Real `ValueError` guard still rejects any fidelity beyond `MAX_TABULATED_EPOCHS`. `analytic_f2` is not actually analytic for this benchmark (documented deviation in its module docstring) — shares one query cache with `query_f1` so a genotype is only looked up once against the real API
- [x] [`substrates/__init__.py`](substrates/__init__.py)
- [x] [`tests/test_substrates.py`](tests/test_substrates.py) — NAS-HPO-Bench-II tests now query the real API, skipped automatically if `data/cache/nashpobench2/` isn't populated in a given environment
- [x] [`configs/search_spaces/jahs_bench_201.yaml`](configs/search_spaces/jahs_bench_201.yaml)
- [x] [`configs/search_spaces/nas_hpo_bench_ii.yaml`](configs/search_spaces/nas_hpo_bench_ii.yaml) — repointed at `nas_hpo_bench_ii_genotype`, not `nas_genotype` (Stage C)

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
- [x] [`methods/sh_emoa.py`](methods/sh_emoa.py) — **moved out of `methods/external/` in Stage C**: no published SH-EMOA package exists to wrap (verified by reading `automl/multi-obj-baselines`, the paper's own reference code — it doesn't use pymoo or anything pip-installable). Real, from-scratch (mu+lambda) EMOA: uniform mutation/crossover, tournament selection, hypervolume-contribution survivor selection (`p3net.metrics.hypervolume`). **Known gap**: only the EMOA half is implemented — the successive-halving/multi-fidelity half needs harness-level multi-fidelity support this project doesn't have yet (same open question as MO-BOHB's fidelity-ladder usage, below)
- [x] [`methods/external/tpe.py`](methods/external/tpe.py) — real `optuna.samplers.TPESampler` via optuna's ask/tell API (Stage C — see the table below for the full story)
- [x] [`methods/external/mo_bohb.py`](methods/external/mo_bohb.py) — real `hpbandster` BOHB config generator + Tchebycheff scalarisation (Stage C — see the table below)
- [x] [`methods/external/_ask_tell_shared.py`](methods/external/_ask_tell_shared.py) — shared `AskTellMethod` (not in the original task list, added to avoid reimplementing the same ask/tell loop twice). `default_valid_sampler` — the Stage-B stand-in sampler this module originally also held — was removed once Stage C wired real backends for both remaining ask/tell arms and it had no callers left
- [x] [`methods/external/__init__.py`](methods/external/__init__.py) — no longer exports `sh_emoa_method`
- [x] [`methods/_shared.py`](methods/_shared.py) — shared rejection-sampling batch generation (used by every arm) + NSGA-II crossover/mutation/survivor-selection helpers (used by `nsga_net.py`/`nsganetv2.py`); not in the original task list, added proactively and then consolidated further during the 5-audit pass (2026-08-14) after the maintainability audit caught the same batch-generation loop duplicated across `p3_absolute.py`/`p3_alone.py`/`random_search.py`
- [x] [`methods/__init__.py`](methods/__init__.py)
- [x] [`configs/methods/*.yaml`](configs/methods/) — all ten (incl. `p3net.yaml`, which configures the library's `p3net.methods.p3net` directly); `model_factory` (a Python callable) is supplied by `scripts/run_experiment.py`, not stored in YAML
- [x] [`tests/test_methods.py`](tests/test_methods.py), [`tests/test_external_wrappers.py`](tests/test_external_wrappers.py) — gaps in the original task list, added
- [x] [`tests/test_sh_emoa.py`](tests/test_sh_emoa.py) — **added in Stage C**: mutation/crossover, dedup, and a from-first-principles cross-check of the hypervolume-contribution survivor-selection logic (its first draft asserted the wrong point should be removed — geometric intuition about "which point is redundant" is unreliable under a nadir-based reference; fixed by computing the expected answer independently via `p3net.metrics.hypervolume` rather than by hand)

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

## Stage C — real benchmark/baseline integration (started 2026-08-15)

Reconnaissance (attempted `uv add` for all five real packages) plus real
wiring where it turned out to be possible:

| Package | Backs | Result |
|---|---|---|
| `nashpobench2api` | NAS-HPO-Bench-II | ✅ **Real.** Installs cleanly (MIT). Dataset (~232MB, `bench12.pkl`/`cellinfo.pkl`/`avgaccs200.pkl`) downloaded via `gdown` from the Google Drive link in its own README, placed at `data/cache/nashpobench2/` (gitignored). `substrates/nas_hpo_bench_ii.py` queries it for real; verified end-to-end with a real `scripts/run_experiment.py` run (`results/raw/random_search__nas_hpo_bench_ii__budget10__seed1.json`). Along the way this surfaced that the real search space differs from what `search_spaces/nas_genotype.py` assumed — see `search_spaces/nas_hpo_bench_ii_genotype.py`, a new module, not a patch to the old one |
| `optuna` | TPE | ✅ **Real.** Installs cleanly (MIT). `methods/external/tpe.py` wraps `optuna.samplers.TPESampler` via optuna's real ask/tell API (`study.ask()`/`study.tell()`), not `optimize()`'s callback style, since this project drives every arm through `p3net.harness.Runner` instead. Every trial optuna is asked for is eventually told something real (never fabricated): FAILED for invalid genotypes, the real cached value for duplicates, or the real evaluation result — leaving a trial permanently un-told would leak optuna-internal state. Supports multi-objective natively (`directions=["minimize"]*n_objectives`), verified with 3 objectives in `tests/test_external_wrappers.py`, not just the paper's 2 |
| `hpbandster` | MO-BOHB | ✅ **Real**, via two workarounds. Install: its hard dependency `netifaces` has no prebuilt wheel for modern Python on Windows and needs MSVC Build Tools to build from source. Verified by reading hpbandster 0.7.4's source that `netifaces` is only ever touched inside a lazy import in `nic_name_to_host()`, used solely by its distributed-worker Pyro4 nameserver (never invoked by the core `BOHB` optimiser) — a local no-op stub package (`vendor/netifaces-stub/`, redirected via `[tool.uv.sources]`) satisfies the dependency without the real C extension. Wiring: the paper's actual MO-BOHB (`automl/multi-obj-baselines`) depends on a custom, unpublished fork of hpbandster with its own multi-objective config generator — not something `pip install hpbandster` gives us. `methods/external/mo_bohb.py` instead wraps the REAL, pip-installed `hpbandster.optimizers.config_generators.bohb.BOHB` (verified by reading its source: fundamentally single-objective, `job.result["loss"]` is one float) with random-weight Tchebycheff scalarisation of `(f1, f2)` into that one loss — the same technique visible in the reference implementation's own (unwired) `MOBOHBWorker.tchebycheff_norm` — a documented adaptation, not a faithful reproduction |
| `pymoo` | (assumed) SH-EMOA | Installed, then **removed**. Reading `automl/multi-obj-baselines` (the paper's own reference code for SH-EMOA/MO-BOHB/guerreroviu2021bagofbaselines) directly showed SH-EMOA is a self-contained (mu+lambda) EA that does not use pymoo or SMS-EMOA at all — "built on SMS-EMOA" (per this project's own paper draft) refers to sharing its hypervolume-contribution survivor-selection *principle*, not shared code. Reimplemented for real in `methods/sh_emoa.py` (see Phase 4) instead of wrapping pymoo |
| `jahs-bench` | JAHS-Bench-201 | ✅ **Real, via a subprocess bridge.** Cannot install in this project's main (Python 3.13) environment at all — hard-pins `scikit-learn>=1.0.2,<1.1.0`, which has no prebuilt wheel for Python ≥3.11 and fails to build from source because its build backend imports `distutils`, removed from the stdlib in Python 3.12. A dedicated Python 3.10 environment (`vendor/jahsbench-env/`, gitignored) installs `jahs-bench==1.1.0` cleanly (also needed a `numpy<2` pin — `uv add` initially picked numpy 2.x, ABI-incompatible with the 2021-era `pandas==1.3.5` wheel jahs-bench pins — and `setuptools<81`, since `pkg_resources` was removed from setuptools in newer releases and old `xgboost==1.5.2` still imports it). Surrogate data (~1.65GB, `assembled_surrogates.tar`) downloaded directly via `curl -C -` with resume (the package's own `download_and_extract_url` buffers the whole file in memory with no retry/resume and failed twice on transient connection drops) from `ml.informatik.uni-freiburg.de`, extracted to `data/cache/jahs_bench_201/` (gitignored) — the separate `metric_data.tar` (~18.7GB, raw per-epoch training data) was **not** downloaded, since only the pretrained surrogates are needed to query. `substrates/jahs_bench_201.py` now queries real data via `vendor/jahsbench-env/query_server.py`, a **persistent** subprocess (JSON-lines over stdin/stdout) rather than one spawned per query — the surrogate models take minutes to load, so a bridge started once and kept alive is required, not optional. `search_spaces/nas_genotype.py` needed NO changes: reading `jahs_bench.lib.core.configspace` directly confirmed its real ConfigSpace matches what that module already assumed (5 ops via the package's own `nb201_to_ops` translation table, `LearningRate`/`WeightDecay` bounds identical to our discretisation grids, `TrivialAugment`/`Activation` choices identical) — only `Optimizer` (fixed to `"SGD"`, not a real search dimension) and the edge-index-to-`Op1..Op6` ordering (JAHS-Bench-201 enumerates the same 6 edges in a different order than `search_spaces/_cell_graph.py`) needed translating, both handled inside `query_server.py` |

- [x] `vendor/netifaces-stub/` — local no-op stub package, documented above
- [x] `vendor/jahsbench-env/` — isolated Python 3.10 venv running jahs-bench for real, bridged via `query_server.py`
- [x] `data/cache/nashpobench2/`, `data/cache/jahs_bench_201/` — real downloaded datasets (gitignored)
- [x] `substrates/jahs_bench_201.py` — real, subprocess-bridged queries; verified end-to-end (`test_jahs_bench_201_live_query_end_to_end`, 343s — almost entirely one-time surrogate-loading cost, confirming the persistent-process design rather than spawn-per-query was the right call). Live-query tests in `tests/test_substrates.py` are opt-in (`RUN_JAHS_BENCH_LIVE_TESTS=1`), not run by default `uv run pytest`
- [x] `methods/external/tpe.py` — real `optuna.samplers.TPESampler`, verified end-to-end (`scripts/run_experiment.py --method tpe --search-space nas_hpo_bench_ii`)
- [x] `methods/external/mo_bohb.py` — real `hpbandster` `BOHB` config generator + Tchebycheff scalarisation, verified end-to-end; `methods/external/_ask_tell_shared.py`'s `default_valid_sampler` removed (no longer used — SH-EMOA/MO-BOHB/TPE are all real now, none need the Stage-B stand-in)

## Open decisions carried into the task list

1. **Best-known-front definition** (`reporting/plots.py`, feeding
   `p3net.metrics.hypervolume`) — candidate is "union of all points
   evaluated by any compared method across all runs"; paper flags this as
   open.
2. **MO-BOHB's fidelity-ladder usage** — ~~open~~ **resolved concretely**:
   `methods/external/mo_bohb.py` always queries at r_K (`FIXED_BUDGET =
   1.0`), never escalating budget, for the same harness-level reason as
   item 3 below. The real config generator (`CG_BOHB.get_config(budget)`)
   is genuinely budget-aware — this is a harness limitation, not a
   limitation of the real algorithm being wrapped.
3. **SH-EMOA's successive-halving half** (`methods/sh_emoa.py`) — the real
   (mu+lambda) EMOA core is implemented; the multi-fidelity budget
   escalation half needs `p3net.harness.Runner`/`substrates.Substrate` to
   support querying below r_K, which they don't yet. The same harness
   change would resolve this and item 2 above together, for real.
