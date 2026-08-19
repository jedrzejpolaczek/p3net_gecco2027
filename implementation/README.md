# implementation

Four independent, repo-ready projects, kept as sibling directories here for
now while the paper (`chapters/v003`) and the code are developed side by
side. Each is structured and scaffolded (`README`, `LICENSE`,
`CODE_OF_CONDUCT`, `CONTRIBUTING`, `SECURITY`, `CHANGELOG`, CI, dependabot)
as if it already were its own repository, so splitting them out later is a
plain `git subtree`/history-preserving extraction, not a rewrite.

- **[`lib/`](lib/README.md)** — `p3net`: the P3 engine (both the batch-
  bootstrap `Pyramid` P3Net uses and the canonical, single-individual-
  climbing `CanonicalPyramid`), the relative linkage-aware surrogate, the
  eLyMPuS/FIHC-eLyMPuS engine, and generic supporting infrastructure.
  Domain-agnostic; knows nothing about NAS or this specific paper. The one
  package the other three below all depend on (via `[tool.uv.sources] p3net
  = { path = "../lib", editable = true }`), never duplicated between them.
- **[`experiments/`](experiments/README.md)** — `p3net-experiments`:
  reproduces the GECCO 2027 paper's main experiment (the 11-arm comparison
  grid, plus the P3Net-vs-`random_search` architecture-only isolation
  experiment and the $\kappa$/threshold sensitivity sweep) on top of `lib/`.
- **[`experiments-bartnik/`](experiments-bartnik/README.md)** —
  `p3net-experiments-bartnik`: a full fork of `experiments/`, isolation
  experiment testing the reconstructed algorithm class Bartnik
  (`bartnik2026evolutionary`) showed separating from baselines on
  architecture-only NAS-Bench-201, run against the same baseline set P3Net
  itself is compared against.
- **[`experiments-przewozniczek/`](experiments-przewozniczek/README.md)** —
  `p3net-experiments-przewozniczek`: a full fork of `experiments/`,
  isolation experiment testing P3-eLyMPuS (`przewozniczek2026lympus`,
  generalised in this project from binary to $k$-ary categorical domains —
  see `notes/lympus-nas-adaptation-literature.md` and
  `notes/lympus-nas-adaptation-validation.md`), same baseline set.

Each has its own `README.md`, `pyproject.toml`, `LICENSE`
(GNU AGPLv3), and the rest of the standard project scaffolding — start
there, not here. This file is only a pointer.

`experiments-bartnik/` and `experiments-przewozniczek/` are literal forks of
`experiments/`: their own `vendor/` and `data/` are Windows directory
junctions back to `experiments/vendor` and `experiments/data` (so the ~3GB
NATS-Bench archive and vendored deps are not duplicated on disk), and each
has its own independent `.venv`/`results/`. Setup for any of the four:
`cd implementation/<package> && uv sync --extra dev`.

## Running the real experiments, at full scale

Every command below is the user's own action to trigger — none of these are
run automatically. Each is a single entry point: smoke test against real
data first (fails fast on a broken environment), then the full grid, then
statistical analysis (Wilcoxon signed-rank + Holm-Bonferroni + Cliff's
delta), writing one `results/*.md` summary. **Do not invoke any of these
files with any command-line argument, not even `--help`** — none of them
parse `argv`, so any argument still runs `main()` in full, i.e. the
expensive real grid.

### 1. Main comparison grid — `experiments/`

The paper's own 11-arm ablation grid across both shared benchmarks
(JAHS-Bench-201 — CIFAR-10, Colorectal-Histology, Fashion-MNIST — and
NAS-HPO-Bench-II), every runnable method, every budget tier, $R=30$ seeds:

```
cd implementation/experiments
uv run python scripts/run_grid.py
```

No flags = every runnable `configs/methods/*.yaml` × every
`configs/search_spaces/*.yaml` (excluding anything marked
`default_grid: false`, e.g. the isolation-experiment search space below) ×
every budget tier in `configs/experiment/budgets.yaml` × every seed.
Skips grid points already persisted under `results/raw/`. Then build the
report's figures/tables from whatever is on disk:

```
uv run python scripts/generate_report.py
```

### 2. Architecture-only NAS-Bench-201 isolation — `experiments/`

Tests whether removing P3Net's own joint architecture+hyperparameter
genotype extension changes the headline result (it does not — see
`conclusions/main.tex`, "Why the results are what they are"):

```
cd implementation/experiments
uv run python scripts/run_nas_bench_201_isolation.py
```

`p3net` vs. `random_search` only, $R=30$ seeds × budgets $\{100, 350\}$ on
`nas_bench_201`. Writes `results/nas_bench_201_isolation_result.md`.

### 3. $\kappa$ / acceptance-threshold sensitivity sweep — `experiments/`

Unlike the two entries above, this one has a real `argparse` CLI (safe to
pass flags, including `--help`) and takes explicit search-space/budget/seed
arguments rather than a single default full-scale command. The paper's own
sweep (`conclusions/main.tex`, "Surrogate error accumulation") covers all
four search spaces and all four budget tiers — reproduce it in full with
one invocation per (search space, budget) pair, e.g.:

```
cd implementation/experiments
uv run python scripts/run_kappa_sensitivity.py --search-space jahs_bench_201 --budget 350 --seeds $(seq 1 30)
```

repeated for `jahs_bench_201`, `jahs_bench_201_colorectal`,
`jahs_bench_201_fashion`, `nas_hpo_bench_ii` × budgets `50 100 200 350`
(16 invocations total for the full grid the paper reports). Each writes its
own per-cell/seed raw JSON under `results/raw/` (`--no-persist` to skip).

### 4. Bartnik-algorithm-class isolation — `experiments-bartnik/`

```
cd implementation/experiments-bartnik
uv run python scripts/run_bartnik_isolation.py
```

`bartnik_p3` vs. the same 9-method baseline set P3Net is compared against
(plus `p3net` itself as a direct engine-vs-engine reference point),
$R=30$ seeds × budgets $\{100, 350\}$ on `nas_bench_201` — 600 real
NATS-Bench queries. Writes `results/bartnik_isolation_result.md`.

### 5. P3-eLyMPuS isolation — `experiments-przewozniczek/`

```
cd implementation/experiments-przewozniczek
uv run python scripts/run_przewozniczek_isolation.py
```

`przewozniczek_p3elympus` vs. the same baseline set, same scale as (4) —
600 real NATS-Bench queries. Writes
`results/przewozniczek_isolation_result.md`.
