from __future__ import annotations

import json
from pathlib import Path

from syntaxgate import cli
from syntaxgate.cli import main


def test_cli_outputs_structured_json(tmp_path, capsys) -> None:
    path = tmp_path / "bad.py"
    path.write_text("def broken(\n", encoding="utf-8")
    assert main([str(path), "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["status"] == "failed"
    assert payload[0]["issues"][0]["line"] == 1


def test_cli_recursive_skips_unknown_files(tmp_path) -> None:
    (tmp_path / "ok.py").write_text("x = 1\n", encoding="utf-8")
    (tmp_path / "notes.txt").write_text("notes", encoding="utf-8")
    assert main([str(tmp_path), "--recursive"]) == 0


def test_staged_mode_uses_index_content(monkeypatch, capsys) -> None:
    monkeypatch.setattr(cli, "_git_files", lambda _: [Path("app.py")])
    monkeypatch.setattr(
        cli.subprocess,
        "check_output",
        lambda *_, **__: b"def broken(\n",
    )
    assert main(["--staged", "--format", "json"]) == 1
    payload = json.loads(capsys.readouterr().out)
    assert payload[0]["path"] == "app.py"
    assert payload[0]["status"] == "failed"
