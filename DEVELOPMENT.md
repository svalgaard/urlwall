# Development Guide

## Setup

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -e ".[test]"
```

## Testing

```bash
pytest -v
```

## Linting

```bash
ruff check .
ruff format --check .
```

## Pre-commit Hooks

This project uses [pre-commit](https://pre-commit.com/) to run linters and formatters automatically before each commit.

### Installation

```bash
pip install pre-commit
pre-commit install
```

This installs hooks that run on every `git commit`:

- **ruff-check** — lints Python code and auto-fixes fixable issues
- **ruff-format** — formats code with ruff's formatter

### Running Manually

```bash
pre-commit run --all-files
```

### Skipping Hooks

If you need to bypass the hooks (not recommended):

```bash
git commit --no-verify -m "skip hooks"
```

## Release Process

1. Bump version in `pyproject.toml`
2. Commit and push to `main`
3. Tag and push:
   ```bash
   git tag v0.1.0
   git push origin v0.1.0
   ```
   The `release.yml` workflow will automatically build and publish to PyPI.
