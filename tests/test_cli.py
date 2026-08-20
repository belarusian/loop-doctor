"""Tests for loop_doctor.cli: exit codes, arg parsing, JSON output."""

from __future__ import annotations

import json
from pathlib import Path

from loop_doctor.cli import main


def _wellformed_gate() -> str:
    """A well-formed gate log: a level-1 title line and a THE SEED block."""
    return chr(10).join([
        "# cycle-001 gate",
        "",
        "## THE SEED",
        "",
        chr(96) * 3,
        "/home/sasha/Research/four",
        chr(96) * 3,
        "",
        "## notes",
        "append-only log",
    ])


def _make_ai_dir(ai_dir: Path) -> None:
    ai_dir.mkdir(parents=True, exist_ok=True)
    (ai_dir / "cycle-001-loop-doctor-gate.md").write_text(
        _wellformed_gate(), encoding="utf-8"
    )
    (ai_dir / "loop-doctor-cycle-runner-prompt.md").write_text(
        "prompt", encoding="utf-8"
    )


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


def test_nonexistent_project_dir_returns_exit_2(tmp_path: Path, capsys) -> None:
    code = main(["check", str(tmp_path / "does-not-exist-xyz-123")])
    assert code == 2
    err = capsys.readouterr().err
    assert "usage error" in err


def test_check_flag_runs_only_that_check(tmp_path: Path, capsys) -> None:
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path), "--check", "foundation", "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert [c["name"] for c in data["checks"]] == ["foundation"]


def test_unknown_check_returns_exit_2(tmp_path: Path, capsys) -> None:
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path), "--check", "nope"])
    assert code == 2
    err = capsys.readouterr().err
    assert "unknown check" in err


def test_go_report_returns_zero(tmp_path: Path, capsys) -> None:
    _make_ai_dir(tmp_path / "ai")
    assert main(["check", str(tmp_path)]) == 0


def test_nogo_report_returns_one(tmp_path: Path, capsys) -> None:
    assert main(["check", str(tmp_path)]) == 1


def test_check_protocol_runs_only_that_check(tmp_path: Path, capsys) -> None:
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path), "--check", "protocol", "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert [c["name"] for c in data["checks"]] == ["protocol"]
    assert data["checks"][0]["status"] == "pass"


def test_check_full_run_composes_both_checks(tmp_path: Path, capsys) -> None:
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path), "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert [c["name"] for c in data["checks"]] == ["foundation", "protocol", "prompt", "bash"]
    assert data["verdict"] is True


def test_check_nogo_when_protocol_fails(tmp_path: Path, capsys) -> None:
    # A malformed gate log (no THE SEED block) makes protocol FAIL -> NO-GO.
    ai_dir = tmp_path / "ai"
    ai_dir.mkdir(parents=True, exist_ok=True)
    (ai_dir / "cycle-001-loop-doctor-gate.md").write_text(
        chr(10).join(["# cycle-001 gate", "", "no seed block here", ""]),
        encoding="utf-8",
    )
    (ai_dir / "loop-doctor-cycle-runner-prompt.md").write_text(
        "prompt", encoding="utf-8"
    )
    code = main(["check", str(tmp_path)])
    assert code == 1
    out = capsys.readouterr().out
    assert "verdict: NO-GO" in out


def test_check_prompt_runs_only_that_check(tmp_path: Path, capsys) -> None:
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path), "--check", "prompt", "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert [c["name"] for c in data["checks"]] == ["prompt"]
    assert data["checks"][0]["status"] == "pass"


def test_check_nogo_when_prompt_fails(tmp_path: Path, capsys) -> None:
    # A runner prompt that passes an unknown flag makes the prompt check FAIL.
    ai_dir = tmp_path / "ai"
    ai_dir.mkdir(parents=True, exist_ok=True)
    (ai_dir / "cycle-001-loop-doctor-gate.md").write_text(
        chr(10).join([
            "# cycle-001 gate",
            "",
            "## THE SEED",
            "",
            chr(96) * 3,
            "/home/sasha/Research/four",
            chr(96) * 3,
            "",
        ]),
        encoding="utf-8",
    )
    spokes_dir = tmp_path / "spokes"
    spokes_dir.mkdir(parents=True, exist_ok=True)
    (spokes_dir / "foo.py").write_text(
        chr(10).join([
            "import argparse",
            "parser = argparse.ArgumentParser()",
            'parser.add_argument("--goal", required=True)',
            "",
        ]),
        encoding="utf-8",
    )
    (ai_dir / "loop-doctor-cycle-runner-prompt.md").write_text(
        f"python {spokes_dir}/foo.py --goal x --bogus y",
        encoding="utf-8",
    )
    code = main(["check", str(tmp_path)])
    assert code == 1
    out = capsys.readouterr().out
    assert "verdict: NO-GO" in out


def test_check_bash_runs_only_that_check(tmp_path: Path, capsys) -> None:
    _make_ai_dir(tmp_path / "ai")
    (tmp_path / "proj").mkdir()
    code = main(["check", str(tmp_path), "--check", "bash", "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert [c["name"] for c in data["checks"]] == ["bash"]
    assert data["checks"][0]["status"] == "pass"


def test_check_nogo_when_bash_fails(tmp_path: Path, capsys) -> None:
    # A .sh driver with a syntax error makes the bash check FAIL -> NO-GO.
    _make_ai_dir(tmp_path / "ai")
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "run.sh").write_text(
        chr(10).join([
            "#!/usr/bin/env bash",
            "if [ -z $x; then",
            "  echo hi",
            "",
        ]),
        encoding="utf-8",
    )
    code = main(["check", str(tmp_path)])
    assert code == 1
    out = capsys.readouterr().out
    assert "verdict: NO-GO" in out
