# C3 — Methods Component

`methods.p3net` is the library's primary export and its sole integration
point: the only component allowed to know about every other one. It wires
`search_engines.p3` (linkage tree, optimal-mixing sweep, pyramid) and
`surrogates` (the relative linkage-aware surrogate) into the full
six-step search loop, implementing `harness.Runner`'s `Method` protocol
so it can be driven generically. See
[C4: P3Net search loop](../c4/p3net-method.md) for the step-by-step
detail this file deliberately stays above.

```mermaid
C4Component
  title Component diagram for methods.p3net

  Component_Ext(problem, "problem", "SearchSpace, Validity, Objectives, dominates/pareto_front")
  Component_Ext(harness, "harness", "EvaluationCache; implements Runner.Method protocol")
  Component_Ext(search_engines_p3, "search_engines.p3", "build_linkage_tree, SweepState, Pyramid")
  Component_Ext(surrogates, "surrogates", "RelativeLinkageAwareSurrogate, telescoped_estimate")

  Container_Boundary(methods, "methods.p3net") {
    Component(p3net, "p3net.py", "P3Net", "propose/update; owns _pyramid and _history (H_t); the one place all four other components meet")
  }

  Rel(p3net, problem, "SearchSpace, Validity, Objectives")
  Rel(p3net, harness, "EvaluationCache dedup + proposal-time duplication tracking")
  Rel(p3net, search_engines_p3, "linkage tree + optimal-mixing sweep + pyramid, rebuilt/consulted once per iteration")
  Rel(p3net, surrogates, "delta_hat_F + telescoped_estimate for step 2-3 acceptance")
```

## Components

| Component | Responsibility | Source |
|---|---|---|
| **p3net.py** | `P3Net`: the full six-step search loop (Proposed Optimizer). By construction the most complex file in the package — the only file carrying documented simplifications | `src/p3net/methods/p3net.py` |

## Why this is the only cross-cutting component

Every other component (`problem`, `harness`, `search_engines.p3`,
`surrogates`, `metrics`) is usable independently — a caller could drive
the linkage tree or a surrogate on its own without `P3Net` existing at
all. `P3Net` is deliberately the single place that assembles all of them
into one runnable algorithm, so that complexity concentrates in one
file with three documented simplifications (two resolved as of
2026-08-15) rather than spreading implicit cross-component coupling
throughout the package.
