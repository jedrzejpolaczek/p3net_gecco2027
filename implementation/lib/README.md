# p3net

![CI](https://github.com/jedrzejpolaczek/p3net/actions/workflows/ci.yml/badge.svg)

A linkage-learning search engine (P3) paired with a relative, linkage-aware
surrogate, for black-box combinatorial (+ optionally discretised-continuous)
optimisation. This is the P3Net algorithm from the GECCO 2027 paper at
`chapters/v003`, packaged as a reusable library rather than as one-off code
tied to that paper's NAS experiment.

See [`TASKS.md`](TASKS.md) for the library's task list in implementation
order.

## Relationship to the experiments repository

`p3net` and its paper reproduction are developed as a matched pair of
repositories, not one project:

- **`p3net` (this repository)** — the P3 engine, the relative
  linkage-aware surrogate, the P3Net method, and the generic infrastructure
  around them (deduplication cache, a pluggable-stopping-rule run driver,
  generic multi-objective metrics). Deliberately domain-agnostic: it has no
  knowledge of neural architecture search, specific benchmarks, or any
  comparison baseline.
- **[`p3net-experiments`](../experiments/README.md)** — reproduces the
  GECCO 2027 paper's actual experiment (JAHS-Bench-201, NAS-HPO-Bench-II,
  the nine-arm ablation grid against NSGA-Net/NSGANetV2/SH-EMOA/MO-BOHB/
  TPE/random search) by consuming this library as a dependency, the same
  way any other user of `p3net` would. Everything specific to that one
  paper — the NAS genotype, the benchmark adapters, the baseline methods,
  the paper's exact statistical plan and reporting — lives there, not here.

Right now both live as sibling directories (`lib/`, `experiments/`) inside
the paper's own repository, for convenience while the paper and the code
are developed side by side. They are structured to split into independent
repositories with no further rework once there's a concrete reason to
(e.g. an external user, independent versioning).

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
- `docs/explanations/` — standalone explainers on P3 and P3Net

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the development workflow, and
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) for community standards.

## License

[GNU AGPLv3](LICENSE).

## Status

Scaffold stage — every file under `src/`, `tests/`, and `pyproject.toml`
currently contains a task list (`TODO` comments), not implementation code,
each referencing the exact paper section it corresponds to. Next step:
[`TASKS.md`](TASKS.md) Phase 1.
