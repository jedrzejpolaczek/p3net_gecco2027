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

See [`docs/architecture/`](docs/architecture/README.md) for the full
C1–C4 architecture documentation.

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

This wires up the real search space, method, harness, and benchmark
substrate end-to-end, and persists the result to `results/raw/`. See
[`tests/test_run_experiment.py`](tests/test_run_experiment.py) and
[`tests/test_run_grid.py`](tests/test_run_grid.py) for the same path
exercised against an in-repo fake substrate.

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the development workflow, and
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) for community standards.

## License

[GNU AGPLv3](LICENSE).

## Status

Fully implemented: concrete NAS search space, benchmark substrate
adapters, NSGA-II, all ten baseline/ablation methods, the stopping rule,
the config-driven run driver (`scripts/run_experiment.py` /
`run_grid.py`), this paper's metrics/statistics, and reporting
(`reporting/*.py` + `scripts/generate_report.py`, rendering
`results/raw/*.json` into the Results-section tables/figures). 149 tests
passing (`uv run pytest`), lint/format clean (`uv run ruff check .` /
`uv run ruff format --check .`). Real benchmark/baseline package
integration is done: JAHS-Bench-201, NAS-HPO-Bench-II, TPE, and MO-BOHB
all query real data/packages, not stand-ins. Known gaps, tracked rather
than silently dropped: the `nsganetv2_continuous` control variant,
`scripts/run_kappa_sensitivity.py` (the kappa/acceptance-threshold sweep
itself — `reporting/plots.py`'s `sensitivity_figure` is ready to consume
its output once it exists), and the archive-turnover diagnostic plot
(needs per-generation population snapshots the harness doesn't persist
yet) — see [`CHANGELOG.md`](CHANGELOG.md). Running the actual R=10-seed
experimental grid and populating the paper's `Results` section with real
numbers has not been done — that's a separate, much larger undertaking
than writing the code that can produce those artifacts once it has real
data to read.
