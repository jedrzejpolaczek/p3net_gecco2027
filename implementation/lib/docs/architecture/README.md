# Architecture Documentation

## Project Overview

`p3net` is a linkage-learning search engine (P3) paired with a relative,
linkage-aware surrogate (δ̂_F), for black-box combinatorial (+ optionally
discretised-continuous) optimisation. It implements the P3Net algorithm
from the GECCO 2027 paper at `chapters/v003`, as a domain-agnostic library
with no knowledge of neural architecture search or any specific benchmark.

## How to Read This Documentation

This documentation follows the **C4 Model**, adapted for a single-package
library rather than a networked, multi-service system:

- **C1: System Context** — `p3net` in relation to the people and systems
  around it (a researcher's code, the `p3net-experiments` package, the
  numeric/ML stack it's built on)
- **C2: Containers** — deliberately thin here: `p3net` is exactly one
  container (one importable Python package), not a distributed system.
  Stated explicitly rather than forced into an artificial split.
- **C3: Components** — the real substance: the six subpackages inside that
  one container, and their dependency graph
- **C4: Code** — class-level deep dives into the two most involved pieces:
  the `P3Net` search loop and the relative linkage-aware surrogate

Start at C1 for the big picture, then descend into the level of detail you
need.

---

## Documentation Index

### C1: System Context

- [System Context Diagram](c1/system-context.md)

### C2: Containers

- [Containers Overview](c2/containers.md)

### C3: Components

The internal structure of the one container: how the six subpackages
depend on each other.

- [Components](c3/components.md)

### C4: Code

| Module | Description |
|---|---|
| [P3Net search loop](c4/p3net-method.md) | The `P3Net` class: propose/update, the six-step search loop, the three documented simplifications |
| [Relative linkage-aware surrogate](c4/relative-surrogate.md) | `RelativeLinkageAwareSurrogate` (δ̂_F) and the telescoping reconstruction — including a real encoding bug found and fixed during implementation |

---

**For questions on specific topics**: browse the C-level that matches your
question's granularity, or see [`../../TASKS.md`](../../TASKS.md) for the
file-by-file implementation record (including gaps and follow-ups).
