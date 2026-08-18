# SyntaxGate

Fast, structured syntax-regression detection for files, standard input, Git
changes, and agent-generated edits.

SyntaxGate uses Python's compiler for Python, native parsers for JSON and TOML,
and Tree-sitter for the remaining supported languages. It is a syntax gate, not
a type checker, linter, formatter, or security scanner.

```console
syntaxgate src/app.py
syntaxgate --language typescript --stdin < src/app.ts
syntaxgate --recursive src --format json
syntaxgate --changed
syntaxgate --staged --format sarif
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

## Supported languages

Python, JavaScript/TypeScript/TSX, Go, Rust, Java, C/C++, C#, Kotlin, Ruby,
PHP, Lua, HTML, CSS, Vue, Svelte, JSON, YAML, TOML, XML, Bash, PowerShell, SQL,
GraphQL, Dockerfile, HCL, and the other grammars supplied by
`tree-sitter-language-pack` that are mapped by extension.

## Origin

SyntaxGate originated in and was battle-tested by
[Grinta](https://github.com/josephsenior/Grinta-Coding-Agent).
