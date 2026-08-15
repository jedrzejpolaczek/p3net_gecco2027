# Architecture Documentation

## Project Overview

`p3net-experiments` reproduces the GECCO 2027 paper's (`chapters/v003`)
experiment: the nine-arm ablation grid plus five additional baselines, on
JAHS-Bench-201 and NAS-HPO-Bench-II. It consumes the
[`p3net`](../../../lib/README.md) library as an ordinary dependency and
adds only what's specific to this one paper.

## How to Read This Documentation

This documentation follows the **C4 Model**, adapted for a single-package
system rather than a networked, multi-service one — the same convention
[`p3net`'s own architecture docs](../../../lib/docs/architecture/README.md)
use:

- **C1: System Context** — `p3net-experiments` in relation to the
  researcher running it, the `p3net` library it builds on, and the real
  benchmarks/baseline packages it queries
- **C2: Containers** — deliberately thin here too: one importable Python
  package plus CLI entry-point scripts, not a distributed system
- **C3: Components** — one file per subsystem: search spaces & substrates,
  methods, harness orchestration, and metrics/statistics/reporting
- **C4: Code** — class-level deep dives into the most algorithmically
  involved pieces: the run pipeline's diagnostics plumbing, SH-EMOA,
  MO-BOHB's Tchebycheff adaptation, and the reporting pipeline's
  best-known-front construction

Start at C1 for the big picture, then descend into the level of detail you
need.

---

## Documentation Index

### C1: System Context

- [System Context Diagram](c1/system-context.md)

### C2: Containers

- [Containers Overview](c2/containers.md)

### C3: Components

| Component | Description |
|---|---|
| [Search Spaces & Substrates](c3/search-spaces-and-substrates.md) | The two benchmarks' genotypes (deliberately not shared) and the real query adapters behind them |
| [Methods](c3/methods.md) | All ten comparison arms: five implemented directly, two wrapping real external optimisers (TPE, MO-BOHB) via a shared ask/tell adapter, plus the NSGA-II engine both NSGA-II-based arms share |
| [Harness Orchestration](c3/harness-orchestration.md) | Configs, the stopping rule, and the `run_experiment.py`/`run_grid.py` CLI entry points tying everything above into a reproducible run |
| [Metrics, Statistics & Reporting](c3/metrics-stats-reporting.md) | This paper's own diagnostics, the statistical comparison plan, and the reporting layer producing the Results-section tables/figures |

### C4: Code

| Module | Description |
|---|---|
| [Run Experiment Pipeline](c4/run-experiment-pipeline.md) | `RunResult`/`persist_run`: why per-run diagnostics needed a wider return type than `p3net`'s own `RunState` |
| [SH-EMOA](c4/sh-emoa.md) | The real (mu+lambda) EMOA, its SMS-EMOA-style hypervolume-contribution survivor selection, and its documented multi-fidelity gap |
| [MO-BOHB Adaptation](c4/mo-bohb-adaptation.md) | Wrapping the real, single-objective `hpbandster` BOHB config generator with Tchebycheff scalarisation |
| [Reporting Pipeline](c4/reporting-pipeline.md) | Best-known-front construction, the reference-point derivation, and why significance is corrected once over the whole comparison set |

---

**For questions on specific topics**: browse the C-level that matches
your question's granularity.
