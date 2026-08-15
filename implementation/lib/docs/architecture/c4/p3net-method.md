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
    +growth_factor: int = 2
    +kappa: int | None
    +acceptance_threshold: float = 0.0
    +objective_index: int = 0
    +analytic_cost: Callable | None = None
    +cache: EvaluationCache
    -_pyramid: Pyramid
    -_history: dict~Genotype, Observation~
    +propose(state) list~Genotype~
    +update(state, new_observations) None
    -_seed_best_objectives(level) None
    -_bootstrap_proposals(level) list~Genotype~
    -_sweep_proposals(level) list~Genotype~
    -_tentatively_accept(surrogate, ancestor, chain, candidate) tuple
    -_diversity_injection(n) list~Genotype~
  }

  class Runner {
    +objective: Callable
    +budget: int
    +stopping_rule: StoppingRule
    +run(method) RunState
  }

  class Pyramid {
    +growth_factor: int
    +levels: list~PyramidLevel~
    +all_stalled: bool
    +add_level() None
    +promote(level_index, genotype, objectives) None
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
  P3Net --> Pyramid : owns the active level (growth on stall)
  P3Net --> SweepState : one per parent, per iteration
  P3Net --> RelativeLinkageAwareSurrogate : rebuilt once per iteration
  P3Net --> EvaluationCache : dedup + proposal-time duplication tracking
  P3Net ..> "search_engines.p3.build_linkage_tree" : rebuilt once per iteration
```

## Class Responsibilities

| Class | Role |
|---|---|
| **P3Net** | Owns `H_t` (`_history`) and the active pyramid level; implements `propose`/`update` so `harness.Runner` can drive it generically. |
| **Runner** | Generic driver, has no P3Net-specific knowledge — counts budget, calls `propose`/`update` in a loop, applies the `StoppingRule`. |
| **Pyramid** | Owns the ordered list of strictly-growing levels; `add_level()` when `all_stalled`, `promote()` records whether the active level's latest evaluated result actually improved on its running best. |
| **SweepState** | One per parent per iteration: walks the linkage subsets in random order, tracks the current (possibly-modified) individual. |
| **RelativeLinkageAwareSurrogate** | δ̂_F, rebuilt from scratch each iteration against the current linkage tree and `H_t`. |
| **EvaluationCache** | Shared dedup cache; also the proposal-time duplication-rate signal (Diagnostics). |

## The Search Loop (`propose` → `Runner` evaluates → `update`)

```mermaid
sequenceDiagram
  participant R as Runner
  participant M as P3Net
  participant PY as Pyramid
  participant LT as linkage_tree
  participant S as RelativeLinkageAwareSurrogate
  participant SW as SweepState

  R->>M: propose(state)
  M->>PY: all_stalled?
  opt current level stalled
    M->>PY: add_level() — new, larger level (growth_factor)
  end
  alt active level not yet full
    M->>M: _bootstrap_proposals(level) — uniform random valid genotypes
  else steady state
    M->>LT: build_linkage_tree(level.population)
    M->>S: fit(H_t, subsets)
    Note over M,S: rebuilt once here, reused for every parent's sweep this iteration
    loop for each parent in level.population
      M->>SW: SweepState.start(parent, tree, level.population, rng)
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
      M->>M: _diversity_injection() — per-pass stall recovery (see Known simplifications)
    end
  end
  R->>R: fully evaluate each proposed genotype (the only budget-consuming step)
  R->>M: update(state, new_observations)
  alt still bootstrapping
    M->>M: fill level.population directly; _seed_best_objectives() once full
  else
    M->>M: fold batch to its single Pareto-best observation
    M->>PY: promote(level_index, best.genotype, best.objectives) — once per batch
  end
  M->>M: cache.put; _history[genotype] = observation; trim level.population to level.size
```

## Known Simplifications

Documented in the module's own docstring (`src/p3net/methods/p3net.py`),
repeated here for visibility:

1. **Single active level, not full simultaneous cross-level cascading.**
   `search_engines.p3.Pyramid` is wired in: `growth_factor` (default 2)
   replaces `population_size`, level 0 starts at `growth_factor`
   individuals, and a new, larger level grows automatically once the
   current level's sweep passes stop improving (`Pyramid.all_stalled`) —
   genuinely "parameter-less". Still simplified relative to canonical
   P3/GOMEA: only the newest level is actively swept; once a level stalls
   and a new one grows, the old level's population is frozen (its
   observations remain in `H_t`, but it is never swept again). A faithful
   multi-level-simultaneous cascade remains a follow-up.
2. **Analytic-cost hook is opt-in.** C* selection is supposed to use
   nondomination in `(f_hat_1, f2)`, with `f2` computed analytically per
   candidate. The optional `analytic_cost: Callable[[Genotype], Objectives]`
   constructor argument does exactly this when supplied; left at its
   default `None`, every non-`f1` objective is still approximated at the
   ancestor's value — correct and complete for single-objective use, a
   documented opt-in-to-fix simplification for multi-objective use.
3. **Stall recovery within one sweep pass is still random reinjection.**
   When a single pass's C* ends up empty after dedup, `_diversity_injection`
   proposes fresh random genotypes for *that pass* rather than triggering
   pyramid growth. This is a different, narrower situation than
   simplification 1's pyramid growth (triggered by a pass completing
   without real improvement, not by a pass yielding zero proposals); both
   mechanisms coexist without conflict.

## A bug found and fixed here during implementation

`Runner` originally treated *any* empty batch from `propose()` as "stop
the whole run" — but a stalled sweep (everything already in `H_t`) is a
legitimate, recoverable state, not a terminal one. Caught by
`tests/test_p3net_integration.py::test_p3net_completes_full_budget_without_error`
failing at exactly the level's population size in evaluations instead of
the requested budget. Fixed by having `P3Net` fall back to
`_diversity_injection` (simplification 3 above) instead of returning an
empty list.

## A design decision made here during the pyramid-wiring follow-up

`update()` calls `Pyramid.promote()` **once per batch, not once per
observation.** A batch can contain a mix of improving and non-improving
results; calling `promote()` for each individually would let a later
non-improving call overwrite an earlier improving one's "not stalled"
signal, incorrectly marking a genuinely improving pass as stalled. Instead
the whole batch folds down to its single Pareto-best observation first
(same `dominates()`-based logic `_seed_best_objectives` uses to establish
the bootstrap baseline), and that one result is what `promote()` sees.
