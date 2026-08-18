from __future__ import annotations

from syntaxgate import check_content, introduced_regression


def test_python_compile_catches_interpreter_phase_errors() -> None:
    result = check_content("bad.py", "return 42\n")
    assert result.failed
    assert result.checker == "python-compile"
    assert result.issues[0].line == 1


def test_json_and_toml_use_native_parsers() -> None:
    assert check_content("ok.json", '{"value": 1}').ok
    broken_json = check_content("bad.json", '{"value": }')
    assert broken_json.failed
    assert broken_json.checker == "json"
    assert check_content("ok.toml", "title = 'ok'\n").ok
    assert check_content("bad.toml", "title = [\n").failed


def test_tree_sitter_checks_javascript() -> None:
    assert check_content("ok.js", "const answer = 42;\n").ok
    result = check_content("bad.js", "function hello( { return 42; }\n")
    assert result.failed
    assert result.checker == "tree-sitter"
    assert result.issues[0].line == 1


def test_unknown_extension_is_explicitly_skipped() -> None:
    result = check_content("notes.unknown", "anything")
    assert result.status == "skipped"
    assert not result.failed


def test_introduced_regression_requires_a_valid_baseline() -> None:
    result = introduced_regression("app.py", "x = 1\n", "def broken(\n")
    assert result.failed
    assert result.introduced is True

    existing = introduced_regression("app.py", "def broken(\n", "def also_broken(\n")
    assert existing.failed
    assert existing.introduced is False
