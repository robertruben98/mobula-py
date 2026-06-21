# Contributing to mobula-py

Thanks for your interest in improving `mobula-py`! Contributions are welcome.

## Getting started

```bash
git clone https://github.com/robertruben98/mobula-py.git
cd mobula-py
python -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Development workflow

This project follows **test-driven development**: write a failing test first,
then the minimal code to pass it.

Before opening a pull request, make sure every gate is green:

```bash
ruff check src tests          # lint
ruff format --check src tests # formatting
mypy --strict src             # static types
pytest                        # unit tests (network is mocked with respx)
```

The CI workflow runs the test suite against Python 3.9–3.13. Keep runtime
annotations compatible with 3.9: do **not** use PEP 604 unions (`X | None`) in
pydantic models or other runtime-evaluated annotations — use
`typing.Optional` / `typing.Union` instead.

### Live integration tests

A single live test hits the real Mobula API and is deselected by default. To run
it you need a (free) API key from [mobula.io](https://mobula.io):

```bash
MOBULA_API_KEY=your-key pytest -m integration
```

## Pull requests

- Keep changes focused and accompanied by tests.
- Update `CHANGELOG.md` under the `[Unreleased]` heading.
- Public methods and models should carry Google-style docstrings and
  `Field(description=...)` metadata.

## Releasing (maintainers)

Releases are published to PyPI automatically via GitHub Actions using Trusted
Publishing (OIDC) when a GitHub Release is published. Bump the version in
`pyproject.toml` and `src/mobula/__init__.py`, update `CHANGELOG.md`, tag, and
publish a release.
