# Contributing to p3net

Thanks for your interest in contributing. See
[`docs/architecture/`](docs/architecture/README.md) for how the library is
structured before picking somewhere to start.

By participating, you agree to abide by the
[Code of Conduct](CODE_OF_CONDUCT.md).

## Getting started

This project uses [`uv`](https://github.com/astral-sh/uv) for dependency
management and packaging.

```bash
git clone https://github.com/jedrzejpolaczek/p3net.git
cd p3net
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

Example: `feat(surrogates): implement relative linkage-aware delta_F`

## Scope boundary

This repository is the `p3net` library only — domain-agnostic search engine
and surrogate code. Anything specific to the GECCO 2027 paper reproduction
(NAS benchmarks, baseline methods, the paper's statistical plan) belongs in
the sibling `experiments` repository instead, which depends on this one.

## License

This project is licensed under the [GNU AGPLv3](LICENSE). By submitting a
contribution, you agree that it will be licensed under the same terms.
