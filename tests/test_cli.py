"""Tests for loop_doctor.cli: exit codes, arg parsing, JSON output."""

from __future__ import annotations

import json
from pathlib import Path

from loop_doctor.cli import main


def _make_ai_dir(ai_dir: Path) -> None:
    ai_dir.mkdir(parents=True, exist_ok=True)
    (ai_dir / "cycle-001-loop-doctor-gate.md").write_text("gate", encoding="utf-8")
    (ai_dir / "loop-doctor-cycle-runner-prompt.md").write_text("prompt", encoding="utf-8")


def test_check_returns_go_when_files_present(tmp_path: Path, capsys) -> None:
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path)])
    assert code == 0
    out = capsys.readouterr().out
    assert "verdict: GO" in out


def test_check_returns_nogo_when_files_missing(tmp_path: Path, capsys) -> None:
    code = main(["check", str(tmp_path)])
    assert code == 1
    out = capsys.readouterr().out
    assert "verdict: NO-GO" in out


def test_check_json_output_parses(tmp_path: Path, capsys) -> None:
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path), "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert data["verdict"] is True
    assert data["checks"][0]["name"] == "foundation"


def test_no_args_returns_usage_error(tmp_path: Path, capsys) -> None:
    code = main([])
    assert code == 2


def test_bad_subcommand_returns_usage_error(tmp_path: Path, capsys) -> None:
    code = main(["frobnicate"])
    assert code == 2


def test_check_from_proj_dir(tmp_path: Path, capsys) -> None:
    (tmp_path / "proj").mkdir()
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path / "proj")])
    assert code == 0
