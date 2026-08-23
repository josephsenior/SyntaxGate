# SyntaxGate

[![CI](https://github.com/josephsenior/SyntaxGate/actions/workflows/ci.yml/badge.svg)](https://github.com/josephsenior/SyntaxGate/actions/workflows/ci.yml)
[![Python 3.10+](https://img.shields.io/badge/python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/license-MIT-green.svg)](LICENSE)

Catch broken syntax before it reaches the next tool, commit, or deployment.

Fast, structured syntax-regression detection for files, standard input, Git
changes, and agent-generated edits.

SyntaxGate uses Python's compiler for Python, native parsers for JSON and TOML,
and Tree-sitter for the remaining supported languages. It is a syntax gate, not
a type checker, linter, formatter, or security scanner.

## Why SyntaxGate?

Generated code and large automated edits can be structurally wrong even when
the change looks reasonable in a diff. SyntaxGate gives those workflows one
small, scriptable check with stable machine-readable output and useful exit
codes.

## Install

```console
python -m pip install syntaxgate
```

For local development:

```console
git clone https://github.com/josephsenior/SyntaxGate.git
cd SyntaxGate
python -m pip install -e ".[dev]"
```

## Usage

```console
syntaxgate src/app.py
syntaxgate --language typescript --stdin < src/app.ts
syntaxgate --recursive src --format json
syntaxgate --changed
syntaxgate --staged --format sarif
```

The command exits with `0` when every selected file passes or is skipped, and
with `1` when at least one file fails. Use `--format json` for integrations or
`--format sarif` for code-scanning-compatible output.

To use it as a lightweight pre-commit hook:

```yaml
repos:
  - repo: https://github.com/josephsenior/SyntaxGate
    rev: main
    hooks:
      - id: syntaxgate
```

## Python API

```python
from syntaxgate import check_content, introduced_regression

before = "def greet(name):\n    return name\n"
after = "def greet(name)\n    return name\n"

result = check_content("greet.py", after)
assert result.failed
assert introduced_regression("greet.py", before, after).introduced
```

Every result has a stable `to_dict()` representation with language, checker,
locations, and issues. Unsupported languages are reported as `skipped`, rather
than silently passed.

## Scope

SyntaxGate validates syntax only. Pair it with your type checker, formatter,
linter, tests, and security scanner for broader coverage.

## Supported languages

Python, JavaScript/TypeScript/TSX, Go, Rust, Java, C/C++, C#, Kotlin, Ruby,
PHP, Lua, HTML, CSS, Vue, Svelte, JSON, YAML, TOML, XML, Bash, PowerShell, SQL,
GraphQL, Dockerfile, HCL, and the other grammars supplied by
`tree-sitter-language-pack` that are mapped by extension.

## Origin

SyntaxGate originated in and was battle-tested by
[Grinta](https://github.com/josephsenior/Grinta-Coding-Agent).

## Contributing

Bug reports, language mappings, documentation improvements, and focused pull
requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md) before opening a
pull request. Security reports should follow [SECURITY.md](SECURITY.md).
