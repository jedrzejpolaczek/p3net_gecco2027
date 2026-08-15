# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).
This project does not yet follow strict [Semantic Versioning](https://semver.org/)
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
  stall recovery) — see the module docstring. Two of the three later
  resolved (below).
- Generic multi-objective metrics (`metrics`): hypervolume (incl. a
  best-known-front fallback), IGD+.
- 92 tests, all passing; lint/format clean.
- `P3Net.analytic_cost: Callable[[Genotype], Objectives] | None = None`
  constructor argument: when supplied, step 4's C* selection computes
  every non-`f1` objective fresh per candidate instead of inheriting the
  ancestor's value; the previous approximation remains the default when
  it isn't supplied (resolves module-docstring simplification 2). See
  `tests/test_p3net_analytic_cost.py`.
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
- `P3Net`: `Pyramid` (Phase 3) is wired in, resolving module-docstring
  simplification 1. `population_size` is gone as a constructor argument;
  `growth_factor: int = 2` now controls level 0's starting size and the
  rate new, larger levels grow at once the current level's sweep passes
  stop improving. Still simplified relative to canonical P3: only the
  newest level actively sweeps, older levels freeze (see the module
  docstring for the exact scope). See
  `tests/test_p3net_pyramid_integration.py` and
  [`docs/architecture/c4/p3net-method.md`](docs/architecture/c4/p3net-method.md).
  Re-measured README's `Results` table under the new behaviour: one seed
  (42) went from beating random search to tying it — a real, documented
  tradeoff of starting from a tiny level 0 instead of a fixed
  reasonably-sized population.
- `surrogates/relative_linkage_aware.py`: `fit()` now encodes each
  distinct genotype once and reuses it across every pair it appears in,
  instead of re-encoding on every pair — `one_hot` was profiled as the
  dominant cost of a 200-budget run (~5.4M redundant calls); after the
  fix, the same run's wall time dropped from 116.53s to 65.55s with
  unchanged behaviour (79/79, now 92/92, tests unaffected — this is a
  black-box-equivalent optimisation).

### Fixed (during implementation, not released separately)

- `RelativeLinkageAwareSurrogate`'s original diff-mask encoding couldn't
  distinguish x→x' from x'→x (opposite-sign deltas); switched to encoding
  both endpoints' values.
- `Runner` treated an iteration where `P3Net` proposed nothing (a stalled
  sweep) as "stop the whole run" instead of "no progress this round";
  `P3Net` now injects fresh random diversity on a stall instead.
