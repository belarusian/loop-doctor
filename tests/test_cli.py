"""Tests for loop_doctor.cli: exit codes, arg parsing, JSON output."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path

import pytest

import loop_doctor.endpoint as endpoint_mod
from loop_doctor import __version__
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
    names = [c["name"] for c in data["checks"]]
    assert names == ["foundation", "protocol", "prompt", "bash", "run_health", "endpoint", "ci"]
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
    pytest.importorskip("spoke_lint")
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path), "--check", "prompt", "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert [c["name"] for c in data["checks"]] == ["prompt"]
    assert data["checks"][0]["status"] == "pass"


def test_check_nogo_when_prompt_fails(tmp_path: Path, capsys) -> None:
    pytest.importorskip("spoke_lint")
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


def test_check_run_health_runs_only_that_check(tmp_path: Path, capsys) -> None:
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path), "--check", "run_health", "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert [c["name"] for c in data["checks"]] == ["run_health"]
    # No cycles.out in the fixture -> SKIP (non-blocking) -> exit 0.
    assert data["checks"][0]["status"] == "skip"


def test_check_nogo_when_run_health_fails(tmp_path: Path, capsys) -> None:
    pytest.importorskip("fourseer")
    # A cycles.out with a missing cycle number makes run_health FAIL -> NO-GO.
    _make_ai_dir(tmp_path / "ai")
    ai_dir = tmp_path / "ai"
    traj_dir = ai_dir / "trajectories"
    traj_dir.mkdir(parents=True, exist_ok=True)
    import json as _json

    for n in (1, 3):
        (traj_dir / f"trajectory_{n:04d}.json").write_text(
            _json.dumps({"outcome": "exit:task_complete", "messages": []}),
            encoding="utf-8",
        )
    nl = chr(10)
    lines = []
    for n in (1, 3):
        lines.append(f"========== CYCLE {n}  10:00:{n:02d}Z ==========")
        lines.append(f"OUTER trajectory saved to: {traj_dir / f'trajectory_{n:04d}.json'}")
        lines.append("OUTER outcome: exit:task_complete")
    (ai_dir / "cycles.out").write_text(nl.join(lines) + nl, encoding="utf-8")
    code = main(["check", str(tmp_path)])
    assert code == 1
    out = capsys.readouterr().out
    assert "verdict: NO-GO" in out


def test_check_endpoint_runs_only_that_check(tmp_path: Path, capsys) -> None:
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path), "--check", "endpoint", "--json"])
    assert code == 0
    data = json.loads(capsys.readouterr().out)
    assert [c["name"] for c in data["checks"]] == ["endpoint"]
    # Default autouse fixture: _probe -> True -> PASS.
    assert data["checks"][0]["status"] == "pass"


def test_check_nogo_when_endpoint_fails(tmp_path: Path, capsys, monkeypatch) -> None:
    # An unreachable endpoint makes the endpoint check FAIL -> NO-GO.
    _make_ai_dir(tmp_path / "ai")
    monkeypatch.setattr(endpoint_mod, "_probe", lambda *a, **k: False)
    code = main(["check", str(tmp_path)])
    assert code == 1
    out = capsys.readouterr().out
    assert "verdict: NO-GO" in out


# ---------------------------------------------------------------------------
# Cycle 8: exit-code contract across all six checks + JSON verdict consistency.
# ---------------------------------------------------------------------------

# The seven registered check names, in stable registration order.
SEVEN_CHECKS = ["foundation", "protocol", "prompt", "bash", "run_health", "endpoint", "ci"]


def _dep_available(name: str) -> bool:
    """Return True if the optional dependency ``name`` is importable."""
    return importlib.util.find_spec(name) is not None


def _seam_foundation(tmp_path: Path, monkeypatch) -> None:
    """Make foundation FAIL: remove the runner prompt (missing 3-file set)."""
    (tmp_path / "ai" / "loop-doctor-cycle-runner-prompt.md").unlink()


def _seam_protocol(tmp_path: Path, monkeypatch) -> None:
    """Make protocol FAIL: rewrite the gate log without a THE SEED block."""
    (tmp_path / "ai" / "cycle-001-loop-doctor-gate.md").write_text(
        "# cycle-001 gate\n\nno seed block here\n", encoding="utf-8"
    )


def _seam_prompt(tmp_path: Path, monkeypatch) -> None:
    """Make prompt FAIL: a runner prompt that passes an unknown flag."""
    spokes_dir = tmp_path / "spokes"
    spokes_dir.mkdir(parents=True, exist_ok=True)
    (spokes_dir / "foo.py").write_text(
        "import argparse\nparser = argparse.ArgumentParser()\n"
        "parser.add_argument('--goal', required=True)\n",
        encoding="utf-8",
    )
    (tmp_path / "ai" / "loop-doctor-cycle-runner-prompt.md").write_text(
        f"python {spokes_dir}/foo.py --goal x --bogus y", encoding="utf-8"
    )


def _seam_bash(tmp_path: Path, monkeypatch) -> None:
    """Make bash FAIL: a .sh driver with a syntax error."""
    proj = tmp_path / "proj"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "run.sh").write_text(
        "#!/usr/bin/env bash\nif [ -z $x; then\n  echo hi\n", encoding="utf-8"
    )


def _seam_run_health(tmp_path: Path, monkeypatch) -> None:
    """Make run_health FAIL: cycles.out with a missing cycle number (1 and 3)."""
    ai_dir = tmp_path / "ai"
    traj_dir = ai_dir / "trajectories"
    traj_dir.mkdir(parents=True, exist_ok=True)
    for n in (1, 3):
        (traj_dir / f"trajectory_{n:04d}.json").write_text(
            json.dumps({"outcome": "exit:task_complete", "messages": []}),
            encoding="utf-8",
        )
    lines = []
    for n in (1, 3):
        lines.append(f"========== CYCLE {n}  10:00:{n:02d}Z ==========")
        lines.append(f"OUTER trajectory saved to: {traj_dir / f'trajectory_{n:04d}.json'}")
        lines.append("OUTER outcome: exit:task_complete")
    (ai_dir / "cycles.out").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _seam_endpoint(tmp_path: Path, monkeypatch) -> None:
    """Make endpoint FAIL: every endpoint unreachable."""
    monkeypatch.setattr(endpoint_mod, "_probe", lambda *a, **k: False)
def _seam_ci(tmp_path: Path, monkeypatch) -> None:
    """Make ci FAIL: a red check run on origin/main head.

    Drives the ``loop_doctor.ci._run`` seam to return canned git/gh results in
    the order ``ci_check`` issues them: inside work tree, a GitHub origin URL,
    fetch ok, rev-parse ok, and a gh check-runs payload with one failure.
    """
    import json as _json
    import subprocess as _subprocess
    import loop_doctor.ci as ci_mod

    sha = "abcdef0123456789abcdef0123456789abcdef01"

    def _cp(rc: int, stdout: str = "", stderr: str = "") -> _subprocess.CompletedProcess:
        return _subprocess.CompletedProcess(args=[], returncode=rc, stdout=stdout, stderr=stderr)

    responses = [
        _cp(0, stdout="true\n"),
        _cp(0, stdout="https://github.com/belarusian/loop-doctor.git\n"),
        _cp(0),
        _cp(0, stdout=sha + "\n"),
        _cp(0, stdout=_json.dumps({"total_count": 1, "check_runs": [
            {"name": "test", "status": "completed", "conclusion": "failure"},
        ]})),
    ]
    it = iter(responses)
    monkeypatch.setattr(ci_mod, "_run", lambda cmd: next(it))


_SEAMS = {
    "foundation": _seam_foundation,
    "protocol": _seam_protocol,
    "prompt": _seam_prompt,
    "bash": _seam_bash,
    "run_health": _seam_run_health,
    "endpoint": _seam_endpoint,
    "ci": _seam_ci,
}


def test_exit_code_zero_when_all_pass_or_skip(tmp_path: Path, capsys) -> None:
    # A well-formed project: every check is PASS or SKIP -> exit 0, verdict true.
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert code == 0
    assert data["verdict"] is True
    assert [c["name"] for c in data["checks"]] == SEVEN_CHECKS
    assert all(c["status"] != "fail" for c in data["checks"])


@pytest.mark.parametrize("check_name", SEVEN_CHECKS)
def test_exit_code_one_when_check_fails(
    check_name: str, tmp_path: Path, capsys, monkeypatch
) -> None:
    # Force the parametrized check to FAIL via its seam -> exit 1, verdict false.
    if check_name == "prompt" and not _dep_available("spoke_lint"):
        pytest.skip("spoke_lint not installed")
    if check_name == "run_health" and not _dep_available("fourseer"):
        pytest.skip("fourseer not installed")
    _make_ai_dir(tmp_path / "ai")
    _SEAMS[check_name](tmp_path, monkeypatch)
    code = main(["check", str(tmp_path), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert code == 1
    assert data["verdict"] is False
    target = next(c for c in data["checks"] if c["name"] == check_name)
    assert target["status"] == "fail"


def test_exit_code_two_for_nonexistent_dir(tmp_path: Path, capsys) -> None:
    code = main(["check", str(tmp_path / "no-such-dir-xyz")])
    assert code == 2
    assert "usage error" in capsys.readouterr().err


def test_exit_code_two_for_unknown_check(tmp_path: Path, capsys) -> None:
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path), "--check", "nope"])
    assert code == 2
    assert "unknown check" in capsys.readouterr().err


def test_json_verdict_matches_exit_code(tmp_path: Path, capsys, monkeypatch) -> None:
    # GO: exit 0 <-> verdict true.
    _make_ai_dir(tmp_path / "ai")
    code = main(["check", str(tmp_path), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert (code == 0) == data["verdict"]
    assert data["verdict"] is True
    # NO-GO: exit 1 <-> verdict false (force endpoint to FAIL).
    monkeypatch.setattr(endpoint_mod, "_probe", lambda *a, **k: False)
    code = main(["check", str(tmp_path), "--json"])
    data = json.loads(capsys.readouterr().out)
    assert (code == 1) == (not data["verdict"])
    assert data["verdict"] is False


# ---------------------------------------------------------------------------
# Cycle 9: --list-checks discovery flag + file-as-project-dir edge case.
# ---------------------------------------------------------------------------

def test_list_checks_prints_registered_names(tmp_path: Path, capsys) -> None:
    # --list-checks prints every registered check name, one per line.
    code = main(["check", "--list-checks"])
    assert code == 0
    out = capsys.readouterr().out
    assert out.splitlines() == SEVEN_CHECKS


def test_list_checks_returns_zero(tmp_path: Path, capsys) -> None:
    assert main(["check", "--list-checks"]) == 0


def test_list_checks_requires_no_project_dir(tmp_path: Path, capsys) -> None:
    # No project dir is passed at all; it must not be required.
    code = main(["check", "--list-checks"])
    assert code == 0
    # Nothing is written to stderr (no usage error).
    assert capsys.readouterr().err == ""


def test_list_checks_runs_no_check(tmp_path: Path, capsys) -> None:
    # --list-checks must not run any check: even a non-existent dir is fine,
    # and the output is the check names, not a report.
    code = main(["check", "--list-checks"])
    out = capsys.readouterr().out
    assert "verdict" not in out
    assert out.splitlines() == SEVEN_CHECKS
    assert code == 0


def test_list_checks_works_with_nonexistent_dir(tmp_path: Path, capsys) -> None:
    # A bogus dir is ignored because no check is run.
    code = main(["check", str(tmp_path / "does-not-exist-xyz-123"), "--list-checks"])
    assert code == 0
    assert capsys.readouterr().out.splitlines() == SEVEN_CHECKS


def test_check_without_dir_or_list_checks_returns_exit_2(tmp_path: Path, capsys) -> None:
    # project_dir is now optional; with neither a dir nor --list-checks it is a usage error.
    code = main(["check"])
    assert code == 2
    assert "usage error" in capsys.readouterr().err


def test_file_as_project_dir_returns_exit_2(tmp_path: Path, capsys) -> None:
    # A regular file (not a dir) passed as the project dir is a usage error -> 2.
    f = tmp_path / "not-a-dir.txt"
    f.write_text("hello", encoding="utf-8")
    code = main(["check", str(f)])
    assert code == 2
    err = capsys.readouterr().err
    assert "usage error" in err
    assert "does not exist" in err

# ---------------------------------------------------------------------------
# Cycle 11: --version top-level flag.
# ---------------------------------------------------------------------------


def test_version_returns_zero(capsys) -> None:
    # --version is a top-level flag: it prints the version and exits 0.
    code = main(["--version"])
    assert code == 0
    out = capsys.readouterr().out
    assert f"loop-doctor {__version__}" in out
    assert "loop-doctor 0.0.1" in out


def test_version_prints_to_stdout_not_stderr(capsys) -> None:
    # The version line goes to stdout; nothing is written to stderr.
    code = main(["--version"])
    assert code == 0
    err = capsys.readouterr().err
    assert err == ""


def test_version_requires_no_project_dir(tmp_path: Path, capsys) -> None:
    # --version must work with no project dir and no subcommand.
    code = main(["--version"])
    assert code == 0
    out = capsys.readouterr().out
    assert "loop-doctor 0.0.1" in out
    # No report is rendered.
    assert "verdict" not in out


def test_version_does_not_break_required_subcommand(capsys) -> None:
    # Adding --version must not break the required-subcommand usage error:
    # main([]) still returns 2.
    code = main([])
    assert code == 2
