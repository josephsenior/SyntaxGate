# Contributing to SyntaxGate

Thanks for helping make syntax checks more dependable.

## Development setup

```console
python -m pip install -e ".[dev]"
python -m pytest -q
python -m ruff check .
python -m build
```

Keep changes focused, add or update tests for behavior changes, and update the
README or changelog when user-facing behavior changes. Supported code should
remain compatible with Python 3.10 and newer.

## Pull requests

Please describe the problem, the approach, and how you verified the change.
Small, reviewable pull requests are easiest to maintain.
