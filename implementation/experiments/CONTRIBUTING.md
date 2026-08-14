# Contributing to p3net-experiments

Thanks for your interest in contributing. This project is at the scaffolding
stage (see [`TASKS.md`](TASKS.md)) — every file currently holds a task list,
not implementation code, and it assumes the `p3net` library is implemented
first (see [`../lib/TASKS.md`](../lib/TASKS.md)). The most useful
contribution right now is picking up one of the experiments tasks in
dependency order.

By participating, you agree to abide by the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Getting started

This project uses [`uv`](https://github.com/astral-sh/uv) for dependency
management and packaging, and depends on `p3net` as a local editable
dependency (see [`pyproject.toml`](pyproject.toml)).

```bash
git clone https://github.com/jedrzejpolaczek/p3net.git
git clone https://github.com/jedrzejpolaczek/p3net-experiments.git
# both must sit as sibling directories for the local dependency path to resolve
cd p3net-experiments
uv sync
```

## Development workflow

Run linting and formatting checks with [`ruff`](https://github.com/astral-sh/ruff):

```bash
uv run ruff check .
uv run ruff format --check .
```

Run the test suite with `pytest`:

```bash
uv run pytest
```

Both are run in CI on every pull request; please make sure they pass locally
before opening one.

## Making a change

1. Open an issue first for anything beyond a small fix, so we can agree on
   the approach before you invest time in it.
2. Create a branch off `dev` (the default development branch — `main` is not
   used for day-to-day work).
3. Keep commits small and focused; write commit messages that explain *why*,
   not just *what*.
4. Add or update tests for any behavior change.
5. Open a pull request against `dev`. Link the issue it addresses.

## Commit messages

This project follows [Conventional Commits](https://www.conventionalcommits.org/en/v1.0.0/):

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

Common types used in this repo:

- `feat` — a new feature
- `fix` — a bug fix
- `docs` — documentation only changes
- `chore` — tooling, config, or repo scaffolding with no source behavior change
- `ci` — changes to CI configuration/workflows
- `test` — adding or correcting tests
- `refactor` — code change that neither fixes a bug nor adds a feature

Example: `feat(substrates): wire JAHS-Bench-201 adapter to fixed r_K resolution`

## Scope boundary

This repository reproduces the GECCO 2027 paper's experiment on top of the
`p3net` library — NAS benchmarks, baseline methods, the paper's statistical
plan and reporting. It must consume `p3net` the way any external user would
(a declared, editable dependency), never via relative imports into the
library's source tree. Anything domain-agnostic belongs upstream in `p3net`
instead.

## License

This project is licensed under the [GNU AGPLv3](LICENSE). By submitting a
contribution, you agree that it will be licensed under the same terms.
