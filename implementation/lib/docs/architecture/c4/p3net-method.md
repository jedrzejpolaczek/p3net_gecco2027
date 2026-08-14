# C4 — P3Net Search Loop

`P3Net` is the library's primary export: it implements `harness.Runner`'s
`Method` protocol (`propose`/`update`), combining the P3 engine
(`search_engines.p3`) and the relative linkage-aware surrogate
(`surrogates.relative_linkage_aware`) into the six-step search loop from
the paper's Proposed Optimizer section.

```mermaid
classDiagram
  class P3Net {
    +search_space: SearchSpace
    +validity: Validity
    +model_factory: Callable
    +rng: random.Random
    +population_size: int = 20
    +kappa: int | None
    +acceptance_threshold: float = 0.0
    +objective_index: int = 0
    +cache: EvaluationCache
    -_population: list~Genotype~
    -_history: dict~Genotype, Observation~
    +propose(state) list~Genotype~
    +update(state, new_observations) None
    -_bootstrap_proposals() list~Genotype~
    -_sweep_proposals() list~Genotype~
    -_tentatively_accept(surrogate, ancestor, chain) tuple
    -_diversity_injection(n) list~Genotype~
  }

  class Runner {
    +objective: Callable
    +budget: int
    +stopping_rule: StoppingRule
    +run(method) RunState
  }

  class SweepState {
    +current: Genotype
    +done: bool
    +propose() Proposal
    +accept(proposal) None
    +reject(proposal) None
  }

  class RelativeLinkageAwareSurrogate {
    +fit(observations, subsets) None
    +predict(x, x_prime, subset) float
  }

  class EvaluationCache {
    +has(genotype, ...) bool
    +put(genotype, value, ...) None
    +record_proposal(genotype, ...) bool
  }

  Runner --> P3Net : drives via Method protocol
  P3Net --> SweepState : one per parent, per iteration
  P3Net --> RelativeLinkageAwareSurrogate : rebuilt once per iteration
  P3Net --> EvaluationCache : dedup + proposal-time duplication tracking
  P3Net ..> "search_engines.p3.build_linkage_tree" : rebuilt once per iteration
```

## Class Responsibilities

| Class | Role |
|---|---|
| **P3Net** | Owns the population and `H_t` (`_history`); implements `propose`/`update` so `harness.Runner` can drive it generically. |
| **Runner** | Generic driver, has no P3Net-specific knowledge — counts budget, calls `propose`/`update` in a loop, applies the `StoppingRule`. |
| **SweepState** | One per parent per iteration: walks the linkage subsets in random order, tracks the current (possibly-modified) individual. |
| **RelativeLinkageAwareSurrogate** | δ̂_F, rebuilt from scratch each iteration against the current linkage tree and `H_t`. |
| **EvaluationCache** | Shared dedup cache; also the proposal-time duplication-rate signal (Diagnostics). |

## The Search Loop (`propose` → `Runner` evaluates → `update`)

```mermaid
sequenceDiagram
  participant R as Runner
  participant M as P3Net
  participant LT as linkage_tree
  participant S as RelativeLinkageAwareSurrogate
  participant SW as SweepState

  R->>M: propose(state)
  alt population not yet full
    M->>M: _bootstrap_proposals() — uniform random valid genotypes
  else steady state
    M->>LT: build_linkage_tree(population)
    M->>S: fit(H_t, subsets)
    Note over M,S: rebuilt once here, reused for every parent's sweep this iteration
    loop for each parent in population
      M->>SW: SweepState.start(parent, tree, population, rng)
      loop until sweep.done or chain reaches kappa
        SW->>M: propose() → candidate on subset F
        M->>M: is_valid(candidate)? reject if not
        M->>S: telescoped_estimate(ancestor, chain + [F], surrogate)
        alt predicted improvement >= acceptance_threshold
          M->>SW: accept(proposal)
        else
          M->>SW: reject(proposal)
        end
      end
    end
    M->>M: pareto_front(candidates, estimated objectives) — C*, this iteration only
    M->>M: cache.record_proposal — dedup
    opt C* empty after dedup
      M->>M: _diversity_injection() — stall recovery (see Known simplifications)
    end
  end
  R->>R: fully evaluate each proposed genotype (the only budget-consuming step)
  R->>M: update(state, new_observations)
  M->>M: cache.put; _history[genotype] = observation; trim population to population_size
```

## Known Simplifications

Documented in the module's own docstring (`src/p3net/methods/p3net.py`),
repeated here for visibility:

1. **Single population, not the full pyramid.** `search_engines.p3.Pyramid`
   is implemented and unit-tested standalone but not yet wired in here;
   `population_size` is a constructor argument, not yet genuinely
   "parameter-less".
2. **No analytic-cost hook.** C* selection is supposed to use
   nondomination in `(f_hat_1, f2)`, with `f2` computed analytically per
   candidate. Objectives other than `f1` are approximated at the
   ancestor's value instead. Correct for single-objective use only.
3. **Stall recovery is random reinjection, not pyramid growth.** When an
   iteration's C* ends up empty after dedup, `_diversity_injection`
   proposes fresh random genotypes rather than triggering the real
   algorithm's pyramid-growth response.

## A bug found and fixed here during implementation

`Runner` originally treated *any* empty batch from `propose()` as "stop
the whole run" — but a stalled sweep (everything already in `H_t`) is a
legitimate, recoverable state, not a terminal one. Caught by
`tests/test_p3net_integration.py::test_p3net_completes_full_budget_without_error`
failing at exactly `population_size` evaluations instead of the requested
budget. Fixed by having `P3Net` fall back to `_diversity_injection`
(simplification 3 above) instead of returning an empty list.
