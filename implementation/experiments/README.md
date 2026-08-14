# p3net-experiments

![CI](https://github.com/jedrzejpolaczek/p3net-experiments/actions/workflows/ci.yml/badge.svg)

Reproduces the experiment described in the GECCO 2027 paper at
`chapters/v003`: the full nine-arm ablation grid (Table `tab:ablation-grid`)
plus five additional baselines, on JAHS-Bench-201 and NAS-HPO-Bench-II.

**This package consumes the [`p3net`](../lib/README.md) library the same
way an external user would** (a local editable dependency on `../lib`,
declared in `pyproject.toml`), not via relative imports into
`../lib/src/p3net`. That boundary is deliberate: it is what makes `../lib`
a real, API-tested library rather than code that merely happens to be
reusable.

See [`TASKS.md`](TASKS.md) for this package's task list in implementation
order (it assumes the library's own [`../lib/TASKS.md`](../lib/TASKS.md) is
implemented first), and [`docs/architecture/`](docs/architecture/README.md)
for a C1 system-context diagram and module map.

## What lives here vs. in the library

Only what is specific to *this paper's* comparison lives here. The P3
engine, the relative linkage-aware surrogate, and the P3Net method itself
are library code (`../lib/src/p3net/`) — this package only adds what's
needed to put P3Net through the paper's specific gauntlet:

- `search_spaces/` — the concrete NAS genotype (six architecture edges +
  discretised training hyperparameters), implementing the library's generic
  `p3net.problem` interfaces
- `substrates/` — JAHS-Bench-201 and NAS-HPO-Bench-II adapters
- `search_engines/nsga2/` — NSGA-II, needed only to build the NSGA-II-based
  baselines below (the library ships only the P3 engine)
- `methods/` — the eight baselines/ablations compared against P3Net
  (`p3net.methods.p3net` itself is library code): NSGA-Net, NSGANetV2,
  P3-alone, P3+absolute-regressor, `random_search.py` (own implementation —
  simple enough to carry no reimplementation risk), and (`methods/external/`,
  ask/tell scaffolding meant to wrap established implementations rather
  than reimplement them; the real pymoo/Optuna/HpBandSter backends are a
  Stage C dependency, not wired up yet) SH-EMOA, MO-BOHB, TPE
- `metrics/` — surrogate-quality (rank correlation) and genotype
  duplication-rate/archive-turnover diagnostics specific to this paper's
  research question (generic hypervolume/IGD+ are library code)
- `stats/` — the paper's specific statistical comparison plan (paired
  Wilcoxon + Holm–Bonferroni + Cliff's delta)
- `reporting/` — tables/plots matching the paper's Results section
- `stopping_rules.py` — the paper's exploration-collapse stopping
  criterion, satisfying the library's generic `StoppingRule` protocol
- `configs/`, `scripts/` — driving the above across the full ablation grid,
  both benchmarks, three budget tiers, ten seeds
- `data/`, `results/` — evaluation cache and generated artifacts (both
  gitignored except placeholders)

## Usage

```bash
uv run python scripts/run_experiment.py \
  --method random_search --search-space nas_hpo_bench_ii --budget 5 --seed 1
```

This wires up the real search space, method, and harness end-to-end. It
currently fails loudly with a `NotImplementedError` from the substrate
(`substrates/nas_hpo_bench_ii.py`), by design: the real benchmark packages
aren't installed yet (Stage C, [`TASKS.md`](TASKS.md)), and the substrate
deliberately refuses to return fake data instead. Every part of the
pipeline up to that boundary — config loading, search space, method,
`p3net.harness.Runner`, result persistence — is real, tested code; see
[`tests/test_run_experiment.py`](tests/test_run_experiment.py) and
[`tests/test_run_grid.py`](tests/test_run_grid.py), which exercise the
same path against an in-repo fake substrate.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the development workflow, and
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) for community standards.

## License

[GNU AGPLv3](LICENSE).

## Status

**Phases 1–6 implemented** (see [`TASKS.md`](TASKS.md) for the detailed
breakdown): concrete NAS search space, benchmark substrate adapters
(structural — real queries deferred to Stage C), NSGA-II, all ten
baseline/ablation methods, the stopping rule, the config-driven run
driver (`scripts/run_experiment.py` / `run_grid.py`), and this paper's
metrics/statistics. 99 tests passing (`uv run pytest`), lint/format clean
(`uv run ruff check .` / `uv run ruff format --check .`). Known gaps,
tracked rather than silently dropped: the `nsganetv2_continuous` control
variant, `scripts/run_kappa_sensitivity.py`, and `reporting/` (Phase 7) —
see [`CHANGELOG.md`](CHANGELOG.md). Stage C (real benchmark/baseline
package integration) has not started.
