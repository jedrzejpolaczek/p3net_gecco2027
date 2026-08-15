# implementation

Two independent, repo-ready projects, kept as sibling directories here for
now while the paper (`chapters/v003`) and the code are developed side by
side. Each is structured and scaffolded (`README`, `LICENSE`,
`CODE_OF_CONDUCT`, `CONTRIBUTING`, `SECURITY`, `CHANGELOG`, CI, dependabot)
as if it already were its own repository, so splitting them out later is a
plain `git subtree`/history-preserving extraction, not a rewrite.

- **[`lib/`](lib/README.md)** — `p3net`: the P3 engine, the relative
  linkage-aware surrogate, the P3Net method, and generic supporting
  infrastructure. Domain-agnostic; knows nothing about NAS or this specific
  paper.
- **[`experiments/`](experiments/README.md)** — `p3net-experiments`:
  reproduces the GECCO 2027 paper's actual experiment on top of `lib/`,
  consumed as a local editable dependency exactly the way an external user
  would.

Each has its own `README.md`, `pyproject.toml`, `LICENSE`
(GNU AGPLv3), and the rest of the standard project scaffolding — start
there, not here. This file is only a pointer.
