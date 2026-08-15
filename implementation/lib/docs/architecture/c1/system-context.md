# C1 — System Context

This diagram shows `p3net` in relation to the people and systems around
it. `p3net` performs no network I/O and holds no persistent state of its
own — everything here is a Python-level (import/call) relationship, not a
network call.

```mermaid
C4Context
  title System Context for p3net

  Person(researcher, "Researcher / Developer", "Imports p3net from Python code to run P3Net (or its individual pieces) against their own black-box combinatorial optimisation problem")

  System(p3net, "p3net", "Linkage-learning search engine (P3) + relative linkage-aware surrogate (delta_hat_F), for black-box combinatorial optimisation")

  System_Ext(p3net_experiments, "p3net-experiments", "Reproduces the GECCO 2027 paper's NAS experiment by consuming p3net as an ordinary dependency")
  System_Ext(numeric_stack, "numpy / scipy / scikit-learn", "Numerical computing and ML primitives p3net's surrogates and linkage tree are built on")

  Rel(researcher, p3net, "Constructs a SearchSpace + Validity + objective, runs P3Net via Runner")
  Rel(p3net_experiments, p3net, "Depends on as a local editable package; supplies the NAS search space, benchmarks, and baselines")
  Rel(p3net, numeric_stack, "Uses for mutual information, regression, linear algebra")

  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## Actors

**Researcher / Developer** — Anyone using `p3net` on their own black-box
combinatorial optimisation problem: defines a `SearchSpace`, a `Validity`
check, and an objective function, then drives `P3Net` (or a smaller piece
of it — the linkage tree, a surrogate, the generic metrics) via
`harness.Runner`. This includes the paper's own authors when reproducing
`chapters/v003`'s results through `p3net-experiments`.

## External Systems

**p3net-experiments** — The GECCO 2027 paper reproduction. Consumes
`p3net` exactly the way any other researcher would (a declared,
local-editable dependency — see its own `pyproject.toml`), never via
relative imports into this package's source tree. Supplies everything
specific to that one paper: the NAS genotype, the JAHS-Bench-201 /
NAS-HPO-Bench-II adapters, the eight comparison baselines, the paper's
exact statistical plan.

**numpy / scipy / scikit-learn** — The only runtime dependencies. `scipy`
and `scikit-learn` back the UPGMA linkage tree (`normalized_mutual_info_score`)
and the two regression-based surrogates; `numpy` is a transitive
dependency of both. No other external system — no database, no API, no
file storage beyond what a caller chooses to do with the returned data.

## Notes

- `p3net` is a pure computation library: given a `SearchSpace`, a
  `Validity` callable, an objective callable, and a budget, it returns an
  observation history. It does not know or care what the caller does with
  the result.
- The GECCO 2027 paper (`chapters/v003`) is the *specification* this
  library implements, not a runtime dependency — there is no diagram node
  for it because C1 documents runtime relationships, not provenance.
- No secrets, no user data, no authentication anywhere in this system —
  confirmed during the maintainability/open-source-readiness audit (full
  git history scan, zero findings beyond the author's own intentionally
  public contact email).
