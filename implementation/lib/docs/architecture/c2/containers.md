# C2 — Containers

`p3net` decomposes into exactly **one container**: a single importable
Python package. This is stated explicitly, not glossed over — C2 exists in
the C4 model to show how a system splits across independently deployable
units, and for a library with no server process, no database, and no
message queue, the honest answer is that it doesn't split. Forcing an
artificial multi-container diagram here would misrepresent the system.
The interesting internal structure lives one level down, at
[C3 — Components](../c3/components.md).

```mermaid
C4Container
  title Container diagram for p3net

  Person(researcher, "Researcher / Developer")
  System_Ext(p3net_experiments, "p3net-experiments")
  System_Ext(numeric_stack, "numpy / scipy / scikit-learn")

  System_Boundary(sb, "p3net") {
    Container(library, "p3net Python package", "Python >=3.11, uv + hatchling", "The entire system: one importable package, no network-facing components, no persistent service, no CLI entry point")
  }

  Rel(researcher, library, "import p3net; construct SearchSpace / P3Net / Runner")
  Rel(p3net_experiments, library, "Local editable dependency, declared in pyproject.toml [tool.uv.sources]")
  Rel(library, numeric_stack, "Calls into for linkage tree, surrogates, metrics")

  UpdateLayoutConfig($c4ShapeInRow="3", $c4BoundaryInRow="1")
```

## The one container

| Container | Technology | Purpose |
|---|---|---|
| **p3net Python package** | Python ≥3.11, packaged with `uv` + `hatchling`, tested with `pytest`, linted/formatted with `ruff` | The library in its entirety: `SearchSpace`/`Genotype` machinery, the P3 engine, both surrogates, the `P3Net` method, the harness (dedup cache, generic `Runner`), and generic multi-objective metrics. Distributed as a normal Python package (`pip install` / `uv add`, or a local editable path for `p3net-experiments`). |

## Why not split further at this level

A library with a single distribution artifact and no runtime process
boundaries doesn't have "containers" in the C4 sense beyond the package
itself — there's no API server to separate from a worker, no database to
separate from application code. Confirmed by inspection during the C1/C2
documentation pass: zero network calls, zero persistent storage, zero
entry points (`grep -rln "if __name__" src/p3net` returns nothing — this
package exposes no CLI or script, only an importable API).

If `p3net` ever grows a second deployable unit — e.g. a CLI wrapper, or a
service exposing search-as-a-service — that's the point this diagram
would gain a second `Container(...)` node. Not before.
