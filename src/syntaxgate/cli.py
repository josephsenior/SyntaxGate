"""Command-line interface for SyntaxGate."""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from collections.abc import Sequence
from pathlib import Path

from .core import SyntaxResult, check_content, check_paths


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="syntaxgate",
        description="Detect syntax regressions in source files and generated edits.",
    )
    parser.add_argument("paths", nargs="*", help="files to validate")
    parser.add_argument("--language", help="override language detection")
    parser.add_argument(
        "--stdin", action="store_true", help="read one document from stdin"
    )
    parser.add_argument("--name", default="stdin", help="path/name to use with --stdin")
    parser.add_argument(
        "--recursive", action="store_true", help="recursively scan paths"
    )
    changes = parser.add_mutually_exclusive_group()
    changes.add_argument(
        "--changed", action="store_true", help="validate changed files"
    )
    changes.add_argument("--staged", action="store_true", help="validate staged files")
    parser.add_argument("--format", choices=("text", "json", "sarif"), default="text")
    return parser


def _git_files(staged: bool) -> list[Path]:
    command = ["git", "diff", "--name-only", "--diff-filter=ACMR"]
    command.extend(["--cached"] if staged else ["HEAD"])
    try:
        output = subprocess.check_output(command, text=True, stderr=subprocess.DEVNULL)
    except (OSError, subprocess.CalledProcessError):
        return []
    return [Path(line) for line in output.splitlines() if line.strip()]


def _staged_results(paths: Sequence[Path], language: str | None) -> list[SyntaxResult]:
    results: list[SyntaxResult] = []
    for path in paths:
        try:
            content = subprocess.check_output(
                ["git", "show", f":{path.as_posix()}"], stderr=subprocess.DEVNULL
            )
        except (OSError, subprocess.CalledProcessError):
            results.append(
                SyntaxResult(str(path), "skipped", detail="staged content unavailable")
            )
            continue
        results.append(check_content(path, content, language=language))
    return results


def _expand(paths: Sequence[str], recursive: bool) -> list[Path]:
    files: list[Path] = []
    for raw in paths:
        path = Path(raw)
        if path.is_file():
            files.append(path)
        elif recursive and path.is_dir():
            files.extend(item for item in path.rglob("*") if item.is_file())
    return files


def _sarif(results: list[SyntaxResult]) -> dict[str, object]:
    sarif_results: list[dict[str, object]] = []
    for result in results:
        for issue in result.issues:
            location: dict[str, object] = {"uri": result.path}
            if issue.line is not None:
                location["region"] = {
                    "startLine": issue.line,
                    "startColumn": issue.column or 1,
                }
            sarif_results.append(
                {
                    "ruleId": issue.kind,
                    "level": "error",
                    "message": {"text": issue.message},
                    "locations": [{"physicalLocation": {"artifactLocation": location}}],
                }
            )
    return {
        "$schema": "https://json.schemastore.org/sarif-2.1.0.json",
        "version": "2.1.0",
        "runs": [
            {"tool": {"driver": {"name": "SyntaxGate"}}, "results": sarif_results}
        ],
    }


def _print_text(results: list[SyntaxResult]) -> None:
    for result in results:
        label = result.status.upper()
        suffix = f" [{result.language}/{result.checker}]" if result.checker else ""
        print(f"{label} {result.path}{suffix}")
        for issue in result.issues:
            position = f"{issue.line}:{issue.column or 1}" if issue.line else ""
            print(f"  {position} {issue.message}".rstrip())
        if result.status == "skipped" and result.detail:
            print(f"  {result.detail}")


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    selected = sum(bool(value) for value in (args.stdin, args.changed, args.staged))
    if selected > 1:
        parser.error("use only one of --stdin, --changed, or --staged")
    if args.stdin:
        results = [
            check_content(args.name, sys.stdin.buffer.read(), language=args.language)
        ]
    elif args.changed or args.staged:
        paths = _git_files(args.staged)
        results = (
            _staged_results(paths, args.language)
            if args.staged
            else check_paths(paths, language=args.language)
        )
    else:
        if not args.paths:
            parser.error("provide a path or use --stdin, --changed, or --staged")
        files = _expand(args.paths, args.recursive)
        results = check_paths(files, language=args.language)

    if args.format == "json":
        print(json.dumps([result.to_dict() for result in results], indent=2))
    elif args.format == "sarif":
        print(json.dumps(_sarif(results), indent=2))
    else:
        _print_text(results)
    return 1 if any(result.failed for result in results) else 0
