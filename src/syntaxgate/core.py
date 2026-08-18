"""Dependency-light syntax validation and regression comparison."""

from __future__ import annotations

import json
import re
from collections.abc import Iterable
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Literal

import tomllib

from .languages import language_for_path

Status = Literal["passed", "failed", "skipped"]


@dataclass(frozen=True, slots=True)
class SyntaxIssue:
    message: str
    line: int | None = None
    column: int | None = None
    kind: str = "syntax_error"

    def to_dict(self) -> dict[str, object]:
        return asdict(self)


@dataclass(frozen=True, slots=True)
class SyntaxResult:
    path: str
    status: Status
    language: str | None = None
    checker: str | None = None
    issues: tuple[SyntaxIssue, ...] = ()
    detail: str = ""
    introduced: bool | None = None

    @property
    def ok(self) -> bool:
        return self.status != "failed"

    @property
    def failed(self) -> bool:
        return self.status == "failed"

    def to_dict(self) -> dict[str, Any]:
        return {
            "path": self.path,
            "status": self.status,
            "ok": self.ok,
            "language": self.language,
            "checker": self.checker,
            "issues": [issue.to_dict() for issue in self.issues],
            "detail": self.detail,
            "introduced": self.introduced,
        }


def check_file(path: str | Path, *, language: str | None = None) -> SyntaxResult:
    target = Path(path)
    try:
        content = target.read_bytes()
    except OSError as error:
        return SyntaxResult(str(target), "skipped", detail=f"file unavailable: {error}")
    return check_content(target, content, language=language)


def check_content(
    path: str | Path,
    content: str | bytes,
    *,
    language: str | None = None,
    max_errors: int = 5,
) -> SyntaxResult:
    """Check one complete source document without writing it to disk."""

    path_text = str(path)
    resolved_language = language_for_path(path_text, language)
    if not resolved_language:
        return SyntaxResult(path_text, "skipped", detail="no parser mapping for path")
    raw = content.encode("utf-8") if isinstance(content, str) else content
    text = raw.decode("utf-8", errors="replace")
    if resolved_language == "python":
        return _python(path_text, text, resolved_language)
    if resolved_language == "json":
        return _json(path_text, text, resolved_language)
    if resolved_language == "toml":
        return _toml(path_text, text, resolved_language)
    return _tree_sitter(path_text, raw, resolved_language, max_errors)


def check_paths(
    paths: Iterable[str | Path], *, language: str | None = None
) -> list[SyntaxResult]:
    return [check_file(path, language=language) for path in paths]


def introduced_regression(
    path: str | Path,
    before: str | bytes,
    after: str | bytes,
    *,
    language: str | None = None,
) -> SyntaxResult:
    """Mark an invalid new document only when it regresses a valid baseline."""

    old = check_content(path, before, language=language)
    new = check_content(path, after, language=language)
    introduced = old.ok and new.failed
    return SyntaxResult(
        path=new.path,
        status=new.status,
        language=new.language,
        checker=new.checker,
        issues=new.issues,
        detail=new.detail,
        introduced=introduced,
    )


def _python(path: str, text: str, language: str) -> SyntaxResult:
    try:
        compile(text, path, "exec")
    except SyntaxError as error:
        issue = SyntaxIssue(
            error.msg or "invalid syntax", error.lineno, error.offset, "python_syntax"
        )
        return _failed(path, language, "python-compile", [issue])
    return SyntaxResult(path, "passed", language, "python-compile")


def _json(path: str, text: str, language: str) -> SyntaxResult:
    try:
        json.loads(text)
    except json.JSONDecodeError as error:
        return _failed(
            path,
            language,
            "json",
            [SyntaxIssue(error.msg, error.lineno, error.colno, "json_syntax")],
        )
    return SyntaxResult(path, "passed", language, "json")


def _toml(path: str, text: str, language: str) -> SyntaxResult:
    try:
        tomllib.loads(text)
    except tomllib.TOMLDecodeError as error:
        line, column = _line_column(str(error))
        return _failed(
            path,
            language,
            "tomllib",
            [SyntaxIssue(str(error), line, column, "toml_syntax")],
        )
    return SyntaxResult(path, "passed", language, "tomllib")


def _tree_sitter(
    path: str, raw: bytes, language: str, max_errors: int
) -> SyntaxResult:
    try:
        from tree_sitter_language_pack import get_parser
    except ImportError:
        return SyntaxResult(path, "skipped", language, detail="tree-sitter unavailable")
    try:
        tree = get_parser(language).parse(raw)
    except Exception as error:
        return SyntaxResult(
            path, "skipped", language, detail=f"parser unavailable: {error}"
        )
    issues = tuple(_tree_issues(tree.root_node, raw, max_errors))
    if issues:
        return _failed(path, language, "tree-sitter", issues)
    return SyntaxResult(path, "passed", language, "tree-sitter")


def _tree_issues(node: Any, source: bytes, max_errors: int) -> list[SyntaxIssue]:
    issues: list[SyntaxIssue] = []

    def visit(current: Any) -> None:
        if len(issues) >= max_errors:
            return
        if current.type == "ERROR" or current.is_missing:
            row, column = current.start_point
            snippet = source[current.start_byte : current.end_byte].decode(
                "utf-8", errors="replace"
            ).replace("\n", "\\n")
            if len(snippet) > 80:
                snippet = snippet[:77] + "..."
            kind = "missing_node" if current.is_missing else "tree_sitter_error"
            message = "missing syntax node" if current.is_missing else "syntax error"
            if snippet:
                message += f": {snippet!r}"
            issues.append(SyntaxIssue(message, row + 1, column + 1, kind))
            return
        for child in current.children:
            visit(child)

    visit(node)
    return issues


def _failed(
    path: str,
    language: str,
    checker: str,
    issues: list[SyntaxIssue] | tuple[SyntaxIssue, ...],
) -> SyntaxResult:
    detail = "; ".join(
        f"line {issue.line}:{issue.column} {issue.message}"
        if issue.line is not None
        else issue.message
        for issue in issues
    )
    return SyntaxResult(path, "failed", language, checker, tuple(issues), detail)


def _line_column(detail: str) -> tuple[int | None, int | None]:
    match = re.search(r"line\s+(\d+)(?:,\s*column\s+(\d+))?", detail, re.I)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2)) if match.group(2) else None
