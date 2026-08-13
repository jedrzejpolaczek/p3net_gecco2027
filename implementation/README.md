# p3net

A linkage-learning search engine (P3) paired with a relative, linkage-aware
surrogate, for black-box combinatorial (+ optionally discretised-continuous)
optimisation. This is the P3Net algorithm from the GECCO 2027 paper at
`chapters/v003`, packaged as a reusable library rather than as one-off code
tied to that paper's NAS experiment.

**Status:** scaffold only. Every file under `src/`, `tests/`, and
`pyproject.toml` currently contains a task list (`TODO` comments) describing
what must be implemented there, referencing the exact paper section it
corresponds to — no implementation code exists yet.

See [`TASKS.md`](TASKS.md) for the library's task list in implementation
order.

## Library vs. experiments

This repository has two parts:

- **`src/p3net/` (this library)** — the P3 engine, the relative
  linkage-aware surrogate, the P3Net method, and the generic infrastructure
  around them (deduplication cache, a pluggable-stopping-rule run driver,
  generic multi-objective metrics). Deliberately domain-agnostic: it has no
  knowledge of neural architecture search, specific benchmarks, or any
  comparison baseline.
- **[`experiments/`](experiments/README.md)** — reproduces the GECCO 2027
  paper's actual experiment (JAHS-Bench-201, NAS-HPO-Bench-II, the nine-arm
  ablation grid against NSGA-Net/NSGANetV2/SH-EMOA/MO-BOHB/TPE/random
  search) by consuming this library as a dependency, the same way any other
  user of `p3net` would. Everything specific to that one paper — the NAS
  genotype, the benchmark adapters, the baseline methods, the paper's exact
  statistical plan and reporting — lives there, not here.

## Layout

- `src/p3net/problem/` — generic search-space machinery: `SearchSpace`/
  `Genotype`, `Decoder`/`Validity` protocols, Pareto dominance, fidelity
  ladder, evaluation-noise handling (Problem Formulation, generalised)
- `src/p3net/search_engines/p3/` — the P3 engine: population pyramid,
  linkage tree (UPGMA over mutual information), optimal mixing sweep
- `src/p3net/surrogates/` — relative linkage-aware `δ̂_F`, absolute
  regressor, telescoping reconstruction
- `src/p3net/methods/p3net.py` — the P3Net method itself: the library's
  primary export, wiring the engine and surrogate into the full search loop
- `src/p3net/harness/` — deduplication cache, seed policy (R vs s), and a
  generic `Runner` with a pluggable `StoppingRule`
- `src/p3net/metrics/` — generic multi-objective indicators: hypervolume,
  IGD+
- `tests/` — one test module per library component
- `docs/explanations/` — existing standalone explainers on P3 and P3Net
  (unchanged)
- `experiments/` — paper reproduction; see its own README
