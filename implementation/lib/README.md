# p3net

![CI](https://github.com/jedrzejpolaczek/p3net/actions/workflows/ci.yml/badge.svg)

A linkage-learning search engine (P3) paired with a relative, linkage-aware
surrogate, for black-box combinatorial (+ optionally discretised-continuous)
optimisation. This is the P3Net algorithm from the GECCO 2027 paper at
`chapters/v003`, packaged as a reusable library rather than as one-off code
tied to that paper's NAS experiment.

See [`TASKS.md`](TASKS.md) for the library's task list, and
[`docs/architecture/`](docs/architecture/README.md) for the C4 architecture
documentation.

## Usage

```python
import random

from sklearn.linear_model import LinearRegression

from p3net import CategoricalDomain, Genotype, P3Net, Runner, SearchSpace

# 1. Define a search space: a Cartesian product of categorical domains.
#    (Continuous coordinates are supported too -- discretise them first
#    with discretize_log_uniform/discretize_linear.)
space = SearchSpace(domains=(CategoricalDomain(values=(0, 1)),) * 12)


# 2. Define the (single-)objective to minimise and a validity check.
def objective(genotype: Genotype) -> tuple[float]:
    return (float(sum(genotype.values)),)  # replace with your real f1


def always_valid(genotype: Genotype) -> float:
    return -1.0  # g(x) <= 0 always; replace with a real constraint check


# 3. Construct P3Net and run it for a fixed full-evaluation budget.
method = P3Net(
    search_space=space,
    validity=always_valid,
    model_factory=LinearRegression,  # any sklearn-style regressor
    rng=random.Random(0),
    population_size=15,
)
state = Runner(objective=objective, budget=200).run(method)

best = min(obs.objectives[0] for obs in state.history)
print(f"best f1 found: {best} ({state.evaluations_used} full evaluations)")
```

See [`tests/test_p3net_integration.py`](tests/test_p3net_integration.py) for
a complete runnable example against a structured toy problem, including a
random-search comparison baseline.

## Results

`tests/test_p3net_integration.py` runs P3Net against a concatenated
deceptive trap-function problem (3 blocks of 4 bits each, global optimum
`f1 = -12`) — the classic benchmark for demonstrating linkage-learning
value, since block-blind search gets stuck at the deceptive
all-zeros-per-block local optimum. Best `f1` found under a 200-evaluation
budget, across 3 independent seeds:

| Seed | P3Net | Random search |
|---|---|---|
| 42 | -11.0 | -9.0 |
| 7 | -10.0 | -8.0 |
| 123 | -10.0 | -10.0 |

P3Net matched or beat random search in every seed, and got noticeably
closer to the known global optimum (`-12.0`) in two of three. This is a
correctness sanity check, not a claim of the algorithm's full strength —
see [`src/p3net/methods/p3net.py`](src/p3net/methods/p3net.py)'s module
docstring for the simplifications this implementation currently carries
relative to the paper's full description.

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
- `docs/architecture/` — C4 architecture documentation
- `docs/explanations/pl/` — standalone explainers on P3 and P3Net (Polish)

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md) for the development workflow, and
[`CODE_OF_CONDUCT.md`](CODE_OF_CONDUCT.md) for community standards.

## License

[GNU AGPLv3](LICENSE).

## Status

**Phases 0–7 implemented** (see [`TASKS.md`](TASKS.md) for the detailed
breakdown): generic search-space machinery, the shared harness, the P3
engine, both surrogates, the full `P3Net` search loop, generic
multi-objective metrics, and top-level API wiring. 79 tests passing
(`uv run pytest`), lint/format clean (`uv run ruff check .` /
`uv run ruff format --check .`). Three documented simplifications remain
(see `methods/p3net.py`'s module docstring) before this matches the
paper's full description; none of them block using the library as
described above.
