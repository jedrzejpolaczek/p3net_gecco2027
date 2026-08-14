# p3net library task index

**Status: Phases 0–7 implemented.** 79/79 tests pass (`uv run pytest`), lint
and format clean (`uv run ruff check .` / `uv run ruff format --check .`).
This file now records what actually landed, including three known
simplifications flagged in `src/p3net/methods/p3net.py`'s module docstring
— read that before building on top of this. Once
[`../experiments/TASKS.md`](../experiments/TASKS.md) needs anything beyond
what's noted here, treat it as a real gap, not an oversight.

## Phase 0 — Environment & scaffolding

- [x] Repo scaffolding — `README.md`, `LICENSE` (AGPLv3), `CODE_OF_CONDUCT.md`,
      `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `.gitattributes`,
      `.gitignore`, `.github/workflows/ci.yml`, `.github/dependabot.yml`
- [x] [`pyproject.toml`](pyproject.toml) — `uv` + `hatchling`, `ruff`,
      `pytest`; core deps are `numpy`, `scipy`, `scikit-learn` (installed,
      `uv.lock` committed)

## Phase 1 — Generic problem machinery

- [x] [`src/p3net/problem/genotype.py`](src/p3net/problem/genotype.py) — `SearchSpace`/`CategoricalDomain`/`Genotype`, `discretize_log_uniform`/`discretize_linear`
- [x] [`src/p3net/problem/decoding.py`](src/p3net/problem/decoding.py) — `Decoder`/`Validity` as plain `Callable` type aliases, `is_valid`/`valid_subset`
- [x] [`src/p3net/problem/objectives.py`](src/p3net/problem/objectives.py) — `dominates`, `pareto_front`, `FidelityLadder`/`FidelityLevel`, `evaluate_with_noise`
- [x] [`src/p3net/problem/__init__.py`](src/p3net/problem/__init__.py)
- [x] [`tests/test_genotype.py`](tests/test_genotype.py), [`tests/test_decoding_validity.py`](tests/test_decoding_validity.py)
- [x] [`tests/test_objectives.py`](tests/test_objectives.py) — gap-filled (not in the original list)

## Phase 2 — Shared harness infrastructure

- [x] [`src/p3net/harness/evaluation_cache.py`](src/p3net/harness/evaluation_cache.py) — `EvaluationCache` keyed on (genotype, experiment type, protocol version); `record_proposal` tracks duplication rate at proposal time
- [x] [`src/p3net/harness/seeds.py`](src/p3net/harness/seeds.py) — `SeedPolicy` (R vs s)
- [x] [`src/p3net/harness/runner.py`](src/p3net/harness/runner.py) — `Runner`, `Method`/`StoppingRule` protocols, `budget_exhausted` default
- [x] [`src/p3net/harness/__init__.py`](src/p3net/harness/__init__.py)
- [x] [`tests/test_evaluation_cache.py`](tests/test_evaluation_cache.py), [`tests/test_runner.py`](tests/test_runner.py)
- [x] [`tests/test_seeds.py`](tests/test_seeds.py) — gap-filled

## Phase 3 — P3 search engine

- [x] [`src/p3net/search_engines/p3/linkage_tree.py`](src/p3net/search_engines/p3/linkage_tree.py) — UPGMA over `sklearn.metrics.normalized_mutual_info_score`, hand-rolled agglomerative merge (not `scipy.cluster.hierarchy`, to keep direct control over the subset-tree output shape)
- [x] [`src/p3net/search_engines/p3/optimal_mixing.py`](src/p3net/search_engines/p3/optimal_mixing.py) — `SweepState` (explicit step-by-step driver, not a generator with `.send()`, for testability); donor provenance left open per the paper's own TODO (donors drawn from whatever `population` the caller passes in)
- [x] [`src/p3net/search_engines/p3/pyramid.py`](src/p3net/search_engines/p3/pyramid.py) — `Pyramid`/`PyramidLevel`, implemented and unit-tested standalone, **but not yet wired into `methods/p3net.py`** (see Phase 5 note)
- [x] [`src/p3net/search_engines/p3/__init__.py`](src/p3net/search_engines/p3/__init__.py), [`src/p3net/search_engines/__init__.py`](src/p3net/search_engines/__init__.py)
- [x] [`tests/test_linkage_tree.py`](tests/test_linkage_tree.py), [`tests/test_optimal_mixing.py`](tests/test_optimal_mixing.py)
- [x] [`tests/test_pyramid.py`](tests/test_pyramid.py) — gap-filled

## Phase 4 — Surrogates

- [x] [`src/p3net/surrogates/absolute_regressor.py`](src/p3net/surrogates/absolute_regressor.py) — one-hot encoding built from an observed-value vocabulary
- [x] [`src/p3net/surrogates/relative_linkage_aware.py`](src/p3net/surrogates/relative_linkage_aware.py) — δ̂_F; trained on one-hot encodings of *both* endpoints concatenated (a same-coordinates-changed diff mask alone can't distinguish x→x' from x'→x, which have opposite-sign deltas — caught by `tests/test_relative_surrogate.py` failing during implementation, fixed)
- [x] [`src/p3net/surrogates/telescoping.py`](src/p3net/surrogates/telescoping.py) — `telescoped_estimate`, `AncestorNotEvaluatedError`
- [x] [`src/p3net/surrogates/_encoding.py`](src/p3net/surrogates/_encoding.py) — internal `build_vocab`/`one_hot`, extracted post-audit: was duplicated verbatim in both `absolute_regressor.py` and `relative_linkage_aware.py` (maintainability-audit finding)
- [x] [`src/p3net/surrogates/__init__.py`](src/p3net/surrogates/__init__.py)
- [x] [`tests/test_relative_surrogate.py`](tests/test_relative_surrogate.py), [`tests/test_telescoping.py`](tests/test_telescoping.py)
- [x] [`tests/test_absolute_regressor.py`](tests/test_absolute_regressor.py) — gap-filled

## Phase 5 — P3Net: the library's primary export

- [x] [`src/p3net/methods/p3net.py`](src/p3net/methods/p3net.py) — full search loop, κ, threshold, telescoping, dedup, constraint handling. **Three documented simplifications** (see the module's own docstring for the full rationale):
  1. Runs over a single fixed-size population, not the full multi-level `Pyramid` from Phase 3 — `population_size` is a constructor argument, not yet genuinely parameter-less.
  2. No analytic-cost hook yet: for objectives other than f1, C* selection approximates them at the ancestor's value rather than freshly computing them for the candidate. Correct for single-objective use; incomplete for real multi-objective (f1, f2) use.
  3. Stall recovery (an iteration where nothing gets accepted) injects fresh random genotypes rather than triggering pyramid growth.
- [x] [`src/p3net/methods/__init__.py`](src/p3net/methods/__init__.py)
- [x] [`tests/test_p3net_integration.py`](tests/test_p3net_integration.py) — gap-filled; end-to-end on a concatenated deceptive trap-function toy problem (the classic linkage-learning benchmark). Caught and fixed a real stall bug (`Runner` treating "no proposals this round" as "stop the whole run"). Confirmed across 3 seeds: P3Net matches or beats random search under an identical budget every time, and gets materially closer to the known global optimum.

## Phase 6 — Generic multi-objective metrics

- [x] [`src/p3net/metrics/hypervolume.py`](src/p3net/metrics/hypervolume.py) — exact, via inclusion-exclusion over the nondominated subset (O(2^k) in front size — fine for this library's scale, not for very large fronts); `hypervolume_relative_to_best_known_front` for the non-enumerable-oracle fallback
- [x] [`src/p3net/metrics/igd_plus.py`](src/p3net/metrics/igd_plus.py)
- [x] [`src/p3net/metrics/__init__.py`](src/p3net/metrics/__init__.py)
- [x] [`tests/test_metrics.py`](tests/test_metrics.py) — includes hand-computed expected values, not just smoke checks

## Phase 7 — Top-level package wiring

- [x] [`src/p3net/__init__.py`](src/p3net/__init__.py) — 40 public names re-exported

## Audit fixes (post-Phase-7, `/audit` run against `implementation/lib`)

Every actionable finding from the maintainability / project-maturity /
production-readiness / open-source-readiness / portfolio-readiness audit
that didn't require pushing to GitHub or committing (see the "not fixed
here" note below):

- [x] Extracted duplicated `_build_vocab`/`_one_hot` into `surrogates/_encoding.py` (maintainability)
- [x] Narrowed both `except Exception` in `methods/p3net.py` to `NoLinkageTreeError` / `AncestorNotEvaluatedError` specifically, with `logging` calls, so an unexpected real bug propagates instead of being silently swallowed (maintainability + production-readiness)
- [x] README: added a runnable `Usage` section (verified to actually execute), a `Results` section with the P3Net-vs-random-search numbers, and corrected the stale `Status` section that claimed "not implemented" (open-source-readiness + portfolio-readiness)
- [x] Added `.github/ISSUE_TEMPLATE/{bug_report,feature_request}.md` and `.github/PULL_REQUEST_TEMPLATE.md` (open-source-readiness)
- [x] Added [`docs/architecture/`](docs/architecture/README.md) — C4 model (adapted for a single-package library: C1 context, C2 containers — explicitly one container, C3 components with the verified dependency graph, C4 code-level deep dives on `P3Net` and the relative surrogate, including both real bugs found during implementation)

**Not fixed here, by design:** the git-history finding (uncommitted work,
non-descriptive commit messages) requires an actual commit, which is a
user decision, not something to do unprompted. The "CI never actually
run" finding requires pushing this to GitHub as its own repo. Both are
tracked, not silently dropped.

## Open decisions carried into the task list

1. **Donor provenance in optimal mixing** (`search_engines/p3/optimal_mixing.py`)
   — must a donor come from H_t, or may it be a transient surrogate-only
   individual? Paper flags this as an open TODO; implemented as
   caller-controlled (whatever `population` is passed to `SweepState.start`)
   rather than hardcoded either way.

Resolved: packaging tool is `uv` + `hatchling`.

## Follow-ups (not gaps in what was asked, but real next steps)

- Wire `Pyramid` into `P3Net` so population size is genuinely parameter-less.
- Add an analytic-cost hook so multi-objective (f1, f2) C* selection freshly
  computes non-f1 objectives per candidate instead of inheriting the
  ancestor's value.
- Performance: linkage tree + surrogate refit every iteration is the
  dominant cost (the 200-budget integration test run takes ~30-60s); fine
  for this library's test scale, worth profiling before real NAS-scale runs.

## After this: experiments/

[`../experiments/TASKS.md`](../experiments/TASKS.md) reproduces the paper's
actual comparison on top of this library. Its Phase 4 (baseline methods)
should double check whether `p3_alone`/`p3_absolute` need the pyramid-growth
follow-up above resolved first, or can proceed with the same single-
population simplification for a first pass.
