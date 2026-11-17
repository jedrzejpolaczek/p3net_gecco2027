# C4 — Run Experiment Pipeline Code

`scripts/run_experiment.py` is the config-to-real-run bridge: it turns a
method YAML file and a search-space YAML file into a constructed `Method`
+ `Substrate` pair, drives them through `p3net.harness.Runner`, and
persists the result — including per-run diagnostics that
[C3: Metrics, Statistics & Reporting](../c3/metrics-stats-reporting.md)'s
`fixed_budget_summary_table`/`p3_alone_sweep_completion_table` need.

```mermaid
classDiagram
  class RunResult {
    <<dataclass, frozen>>
    +state: RunState
    +cache: EvaluationCache
    +method: Any
  }

  class ModuleFunctions {
    <<module-level functions>>
    +build_search_space(search_space_config)$ tuple~SearchSpace, Validity~
    +build_substrate(search_space_config)$ Substrate
    +build_method(method_config, search_space, validity, rng, cache)$ Method
    +run_single(method_config, search_space_config, budget, seed)$ RunResult
    +result_path(method_name, search_space_name, budget, seed)$ Path
    +persist_run(result, method_name, search_space_name, budget, seed)$ Path
  }

  class Runner {
    <<p3net.harness.runner>>
    +objective: Callable
    +budget: int
    +stopping_rule: StoppingRule
    +run(method) RunState
  }

  class Substrate {
    <<p3net ABC, substrates.base>>
    +objectives(genotype) Objectives
  }

  ModuleFunctions --> RunResult : run_single() returns
  ModuleFunctions --> Runner : constructs, drives via Runner.run(method)
  ModuleFunctions --> Substrate : objective=substrate.objectives
  RunResult --> Runner : state: RunState
```

## Function Responsibilities

| Function | Role |
|---|---|
| **build_search_space** | Dispatches on `search_space_config["search_space"]` via `_SEARCH_SPACE_BUILDERS` — one entry per benchmark's genotype module |
| **build_substrate** | Dispatches on `search_space_config["substrate"]` via `_SUBSTRATE_BUILDERS` |
| **build_method** | Dispatches on `method_config["method"]`; constructs the named arm with `search_space`/`validity`/`rng`/`cache` plus whatever `params` the YAML supplies. Raises `NotImplementedError` for a `not_yet_implemented` config rather than silently running the wrong thing |
| **run_single** | Builds everything, constructs a `Runner` with `BudgetOrExplorationCollapse`, runs it, returns a `RunResult` |
| **persist_run** | Serialises `RunResult.state.history` to JSON plus a `"diagnostics"` object (`cache.duplication_rate`, and `method.sweeps_completed` if the method exposes it) |

## Why `run_single` returns `RunResult`, not a bare `RunState`

`p3net.harness.runner.RunState` only carries `history`/`evaluations_used`
— the generic contract `Runner` needs. `persist_run` needs more: the
`EvaluationCache`'s `duplication_rate` and, for `P3Alone` specifically,
`sweeps_completed`. Both live on objects `run_single` constructs
internally (`cache`, `method`) but previously discarded once `Runner.run`
returned. `RunResult` just keeps them alive one level up, in
`experiments/`-owned code — `p3net.harness.runner.RunState` itself is
untouched, keeping this experiment-specific need out of library code.
This had a small ripple: `run_grid.py` and 4 call sites in
`tests/test_run_experiment.py` updated to read `result.state.x` instead
of `state.x`.

## The persisted JSON schema

```json
{
  "method": "p3net",
  "search_space": "jahs_bench_201",
  "budget": 200,
  "seed": 1,
  "evaluations_used": 200,
  "history": [{"genotype": [...], "objectives": [...]}, ...],
  "diagnostics": {"duplication_rate": 0.12, "sweeps_completed": 4}
}
```

`"diagnostics"` is additive: `reporting/_common.py::load_raw_run` defaults
it to `{}` for files persisted before this field existed, so old and new
raw runs both load correctly without a migration step.
