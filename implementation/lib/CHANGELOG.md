# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to the phase-based scaffolding described in
[`TASKS.md`](TASKS.md) rather than strict [Semantic Versioning](https://semver.org/)
until a first `0.1.0` release is reached.

## [Unreleased]

### Added

- Generic search-space machinery (`problem`): `SearchSpace`, `Genotype`,
  `Decoder`/`Validity` protocols, Pareto dominance/front, fidelity ladder,
  evaluation-noise handling.
- Shared harness (`harness`): `EvaluationCache`, `SeedPolicy`, generic
  `Runner` with a pluggable `StoppingRule`.
- P3 search engine (`search_engines.p3`): UPGMA linkage tree over
  normalised mutual information, optimal-mixing sweep, population pyramid.
- Surrogates (`surrogates`): absolute regressor, relative linkage-aware
  δ̂_F, telescoping chain reconstruction.
- `P3Net` (`methods.p3net`): the full search loop, with three documented
  simplifications (single population rather than the full pyramid, no
  analytic-cost hook for multi-objective C* selection, random-reinjection
  stall recovery) — see the module docstring.
- Generic multi-objective metrics (`metrics`): hypervolume (incl. a
  best-known-front fallback), IGD+.
- 79 tests, all passing; lint/format clean.
- [`docs/architecture/`](docs/architecture/README.md): C4 model
  documentation (context, containers, components, and two code-level deep
  dives), adapted for a single-package library.
- README: runnable `Usage` example and a `Results` section with real
  P3Net-vs-random-search benchmark numbers.
- `.github/ISSUE_TEMPLATE/`, `.github/PULL_REQUEST_TEMPLATE.md`.

### Changed

- `surrogates/_encoding.py`: `build_vocab`/`one_hot` extracted out of
  `absolute_regressor.py` and `relative_linkage_aware.py`, which had
  duplicated the same encoding logic verbatim (maintainability-audit
  finding).
- `methods/p3net.py`: both `except Exception` blocks narrowed to the
  specific exception each site can legitimately expect
  (`NoLinkageTreeError`, `AncestorNotEvaluatedError`), with `logging`
  calls, so an unrelated real bug propagates instead of being silently
  swallowed (maintainability + production-readiness audit findings).

### Fixed (during implementation, not released separately)

- `RelativeLinkageAwareSurrogate`'s original diff-mask encoding couldn't
  distinguish x→x' from x'→x (opposite-sign deltas); switched to encoding
  both endpoints' values.
- `Runner` treated an iteration where `P3Net` proposed nothing (a stalled
  sweep) as "stop the whole run" instead of "no progress this round";
  `P3Net` now injects fresh random diversity on a stall instead.
