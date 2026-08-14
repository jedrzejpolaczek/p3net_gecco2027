# p3net library task index

Every file below currently contains only a task list (`TODO` comments), not
implementation code. This file orders those tasks into a build sequence for
**the library only** (`src/p3net/`) — domain-agnostic code with no knowledge
of NAS, specific benchmarks, or comparison baselines. Once this is
implemented, [`../experiments/TASKS.md`](../experiments/TASKS.md) picks up and
reproduces the actual GECCO 2027 paper by consuming this library as a
dependency.

## Phase 0 — Environment & scaffolding

- [x] Repo scaffolding — `README.md`, `LICENSE` (AGPLv3), `CODE_OF_CONDUCT.md`,
      `CONTRIBUTING.md`, `SECURITY.md`, `CHANGELOG.md`, `.gitattributes`,
      `.gitignore`, `.github/workflows/ci.yml`, `.github/dependabot.yml`
- [x] [`pyproject.toml`](pyproject.toml) — manifest scaffolded (`uv` +
      `hatchling`, `ruff`, `pytest`); `dependencies = []` still to be filled
      in as Phase 1+ lands

## Phase 1 — Generic problem machinery

Nothing else can be written before this exists: the search engine needs a
genotype to vary, surrogates need objectives to predict, the runner needs a
budget/objective contract to drive.

- [ ] [`src/p3net/problem/genotype.py`](src/p3net/problem/genotype.py) — generic `SearchSpace`/`Genotype`
- [ ] [`src/p3net/problem/decoding.py`](src/p3net/problem/decoding.py) — `Decoder`/`Validity` protocols
- [ ] [`src/p3net/problem/objectives.py`](src/p3net/problem/objectives.py) — Pareto dominance/front, fidelity ladder, noise handling
- [ ] [`src/p3net/problem/__init__.py`](src/p3net/problem/__init__.py) — re-export public API
- [ ] [`tests/test_genotype.py`](tests/test_genotype.py) — against a synthetic search space, not NAS
- [ ] [`tests/test_decoding_validity.py`](tests/test_decoding_validity.py) — against a synthetic Decoder/Validity, not NAS

## Phase 2 — Shared harness infrastructure (cache, seeds, runner)

Depend only on `problem/` (genotype hashing/equality for cache keys, the
generic objective contract for the runner).

- [ ] [`src/p3net/harness/evaluation_cache.py`](src/p3net/harness/evaluation_cache.py) — dedup cache, proposal-time duplication counting
- [ ] [`src/p3net/harness/seeds.py`](src/p3net/harness/seeds.py) — R vs s seed policy
- [ ] [`src/p3net/harness/runner.py`](src/p3net/harness/runner.py) — generic `Runner` + `StoppingRule` protocol (default: budget exhaustion)
- [ ] [`src/p3net/harness/__init__.py`](src/p3net/harness/__init__.py)
- [ ] [`tests/test_evaluation_cache.py`](tests/test_evaluation_cache.py)
- [ ] [`tests/test_runner.py`](tests/test_runner.py) — must prove `StoppingRule` is genuinely pluggable, not accidentally hardcoded

## Phase 3 — P3 search engine

Depends on `problem/` (genotype) and `harness/` (dedup, for realistic sweep
testing). Must exist before any surrogate can be linkage-aware.

- [ ] [`src/p3net/search_engines/p3/linkage_tree.py`](src/p3net/search_engines/p3/linkage_tree.py) — UPGMA over mutual information
- [ ] [`src/p3net/search_engines/p3/optimal_mixing.py`](src/p3net/search_engines/p3/optimal_mixing.py) — crossover sweep, acceptance-agnostic
- [ ] [`src/p3net/search_engines/p3/pyramid.py`](src/p3net/search_engines/p3/pyramid.py) — population pyramid, growth rule
- [ ] [`src/p3net/search_engines/p3/__init__.py`](src/p3net/search_engines/p3/__init__.py)
- [ ] [`src/p3net/search_engines/__init__.py`](src/p3net/search_engines/__init__.py)
- [ ] [`tests/test_linkage_tree.py`](tests/test_linkage_tree.py)
- [ ] [`tests/test_optimal_mixing.py`](tests/test_optimal_mixing.py)

## Phase 4 — Surrogates

`absolute_regressor.py` depends only on `problem/`. `relative_linkage_aware.py`
additionally depends on the linkage tree (Phase 3), since δ̂_F is defined
only given linkage subsets F. `telescoping.py` depends on
`relative_linkage_aware.py`.

- [ ] [`src/p3net/surrogates/absolute_regressor.py`](src/p3net/surrogates/absolute_regressor.py)
- [ ] [`src/p3net/surrogates/relative_linkage_aware.py`](src/p3net/surrogates/relative_linkage_aware.py) — δ̂_F
- [ ] [`src/p3net/surrogates/telescoping.py`](src/p3net/surrogates/telescoping.py) — chain reconstruction back to H_t ancestor
- [ ] [`src/p3net/surrogates/__init__.py`](src/p3net/surrogates/__init__.py)
- [ ] [`tests/test_relative_surrogate.py`](tests/test_relative_surrogate.py)
- [ ] [`tests/test_telescoping.py`](tests/test_telescoping.py)

## Phase 5 — P3Net: the library's primary export

Depends on everything above: the engine (Phase 3), the surrogate (Phase 4),
and the harness (Phase 2).

- [ ] [`src/p3net/methods/p3net.py`](src/p3net/methods/p3net.py) — full search loop, κ, telescoping, constraint handling
- [ ] [`src/p3net/methods/__init__.py`](src/p3net/methods/__init__.py)

## Phase 6 — Generic multi-objective metrics

Independent of Phases 3–5 (pure functions over objective vectors) — could
be built any time after Phase 1, but ordered last since nothing else
depends on it.

- [ ] [`src/p3net/metrics/hypervolume.py`](src/p3net/metrics/hypervolume.py) — incl. externally-supplied-reference-front support
- [ ] [`src/p3net/metrics/igd_plus.py`](src/p3net/metrics/igd_plus.py)
- [ ] [`src/p3net/metrics/__init__.py`](src/p3net/metrics/__init__.py)
- [ ] [`tests/test_metrics.py`](tests/test_metrics.py)

## Phase 7 — Top-level package wiring

- [ ] [`src/p3net/__init__.py`](src/p3net/__init__.py) — re-export final public API once every submodule above exists

## Open decisions carried into the task list

1. **Donor provenance in optimal mixing** (`search_engines/p3/optimal_mixing.py`)
   — must a donor come from H_t, or may it be a transient surrogate-only
   individual? Paper flags this as an open TODO.

Resolved: packaging tool is `uv` + `hatchling` (matches the repo scaffolding
in Phase 0; `../experiments/pyproject.toml` depends on this package locally
and editably via `[tool.uv.sources]`).

## After this: experiments/

Once Phases 0–7 above are implemented and the library's public API
(`src/p3net/__init__.py`) is stable enough to build against,
[`../experiments/TASKS.md`](../experiments/TASKS.md) reproduces the paper's actual
comparison on top of it.
