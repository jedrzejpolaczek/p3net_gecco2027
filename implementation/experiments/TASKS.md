# Experiments task index (GECCO 2027 paper reproduction)

Every file below currently contains only a task list (`TODO` comments), not
implementation code. This assumes the `p3net` library ([`../lib/TASKS.md`](../lib/TASKS.md))
is already implemented and installed here as a local editable dependency on
`../lib` (`experiments/pyproject.toml`) — every phase below imports it as
`p3net.*`, never via a relative path into `../lib/src/p3net`.

## Phase 0 — Environment & scaffolding

- [x] Repo scaffolding — `README.md`, `LICENSE` (AGPLv3), `CODE_OF_CONDUCT.md`,
      `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `.gitattributes`,
      `.gitignore`, `.github/workflows/ci.yml`, `.github/dependabot.yml`
- [x] [`pyproject.toml`](pyproject.toml) — manifest scaffolded, incl. the
      local editable `p3net` dependency (`[tool.uv.sources]`); benchmark/
      baseline deps still to be filled in as Phase 2/4 lands

## Phase 1 — Concrete NAS search space

Implements the library's generic `p3net.problem` interfaces for this
paper's domain. Nothing benchmark- or method-specific can be written before
this exists.

- [ ] [`search_spaces/nas_genotype.py`](search_spaces/nas_genotype.py) — six architecture edges + discretised Θ, plus the continuous-Θ control variant
- [ ] [`search_spaces/__init__.py`](search_spaces/__init__.py)
- [ ] [`tests/test_nas_search_space.py`](tests/test_nas_search_space.py)

## Phase 2 — Benchmark substrates

Depend on `search_spaces/` for the concrete genotype they translate to/from
each benchmark's own query format.

- [ ] [`substrates/base.py`](substrates/base.py) — common query interface, fidelity ladder exposure
- [ ] [`substrates/jahs_bench_201.py`](substrates/jahs_bench_201.py) — Category 2 adapter
- [ ] [`substrates/nas_hpo_bench_ii.py`](substrates/nas_hpo_bench_ii.py) — Category 1 adapter
- [ ] [`substrates/__init__.py`](substrates/__init__.py)
- [ ] [`tests/test_substrates.py`](tests/test_substrates.py)
- [ ] [`configs/search_spaces/jahs_bench_201.yaml`](configs/search_spaces/jahs_bench_201.yaml)
- [ ] [`configs/search_spaces/nas_hpo_bench_ii.yaml`](configs/search_spaces/nas_hpo_bench_ii.yaml)

## Phase 3 — NSGA-II (needed only for baselines)

Depends on `search_spaces/` (genotype). Independent of Phase 2, can be built
in parallel with it.

- [ ] [`search_engines/nsga2/nondominated_sort.py`](search_engines/nsga2/nondominated_sort.py)
- [ ] [`search_engines/nsga2/crowding_distance.py`](search_engines/nsga2/crowding_distance.py)
- [ ] [`search_engines/nsga2/__init__.py`](search_engines/nsga2/__init__.py)
- [ ] [`search_engines/__init__.py`](search_engines/__init__.py)

## Phase 4 — Baseline/ablation methods

Each depends on `p3net.search_engines.p3` / `p3net.surrogates.*` (library,
already implemented) or `experiments.search_engines.nsga2` (Phase 3), plus
`substrates/` (Phase 2) as the objective source. Ordered simplest-first.

- [ ] [`methods/nsga_net.py`](methods/nsga_net.py) — NSGA-II, no surrogate
- [ ] [`methods/p3_alone.py`](methods/p3_alone.py) — P3 (library), no surrogate, real-eval-gated sweep
- [ ] [`methods/nsganetv2.py`](methods/nsganetv2.py) — NSGA-II + absolute regressor (+ continuous-Θ control)
- [ ] [`methods/p3_absolute.py`](methods/p3_absolute.py) — P3 (library) + absolute regressor
- [ ] [`methods/random_search.py`](methods/random_search.py) — own implementation, not a wrapper (too simple to carry reimplementation risk)
- [ ] [`methods/external/tpe.py`](methods/external/tpe.py)
- [ ] [`methods/external/sh_emoa.py`](methods/external/sh_emoa.py)
- [ ] [`methods/external/mo_bohb.py`](methods/external/mo_bohb.py)
- [ ] [`methods/external/__init__.py`](methods/external/__init__.py)
- [ ] [`methods/__init__.py`](methods/__init__.py)
- [ ] [`configs/methods/*.yaml`](configs/methods/) — all ten (incl. `p3net.yaml`, which configures the library's `p3net.methods.p3net` directly)

## Phase 5 — Stopping rule + run driver + experiment configs

`stopping_rules.py` implements `p3net.harness.runner`'s `StoppingRule`
protocol (library, already implemented). Depends on Phases 1–4 all being in
place, since the driver runs an arbitrary method against an arbitrary
substrate.

- [ ] [`stopping_rules.py`](stopping_rules.py) — exploration-collapse criterion
- [ ] [`configs/experiment/budgets.yaml`](configs/experiment/budgets.yaml)
- [ ] [`configs/experiment/kappa_threshold_sweep.yaml`](configs/experiment/kappa_threshold_sweep.yaml)
- [ ] [`scripts/run_experiment.py`](scripts/run_experiment.py) — single run entry point
- [ ] [`scripts/run_grid.py`](scripts/run_grid.py) — full ablation-grid sweep
- [ ] [`scripts/run_kappa_sensitivity.py`](scripts/run_kappa_sensitivity.py)

## Phase 6 — Metrics & statistics

Consume the H_t / run records produced by Phase 5.

- [ ] [`metrics/surrogate_quality.py`](metrics/surrogate_quality.py) — rank correlation vs |H_t|
- [ ] [`metrics/diagnostics.py`](metrics/diagnostics.py) — duplication rate, archive turnover
- [ ] [`metrics/__init__.py`](metrics/__init__.py)
- [ ] [`tests/test_experiment_metrics.py`](tests/test_experiment_metrics.py)
- [ ] [`stats/significance.py`](stats/significance.py) — paired Wilcoxon + Holm–Bonferroni + Cliff's delta
- [ ] [`stats/__init__.py`](stats/__init__.py)

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
