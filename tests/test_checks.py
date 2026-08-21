"""Tests for loop_doctor.checks: registry composition and aggregate verdict."""

from __future__ import annotations

from pathlib import Path

import pytest

import loop_doctor.endpoint as endpoint_mod
from loop_doctor.checks import register, run_all
from loop_doctor.report import Check, Report, Status


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


def test_run_all_returns_foundation_check(tmp_path: Path) -> None:
    _make_ai_dir(tmp_path / "ai")
    checks = run_all(tmp_path)
    assert isinstance(checks, list)
    names = [c.name for c in checks]
    assert "foundation" in names
    foundation = next(c for c in checks if c.name == "foundation")
    assert foundation.status is Status.PASS


def test_run_all_foundation_fails_when_files_missing(tmp_path: Path) -> None:
    checks = run_all(tmp_path)
    foundation = next(c for c in checks if c.name == "foundation")
    assert foundation.status is Status.FAIL
    assert "gate log" in foundation.detail
    assert "runner prompt" in foundation.detail


def test_registering_second_check_makes_run_all_return_both_in_stable_order(
    tmp_path: Path,
) -> None:
    _make_ai_dir(tmp_path / "ai")

    def _second(project_dir: Path) -> Check:
        return Check("second", Status.PASS, "ok")

    register("second", _second)
    try:
        checks = run_all(tmp_path)
        names = [c.name for c in checks]
        # foundation and protocol are registered at import time, so they
        # come first; the dynamically registered "second" comes last.
        assert names == [
            "foundation", "protocol", "prompt", "bash", "run_health", "endpoint", "ci", "second",
        ]
        # stable across repeated calls
        assert [c.name for c in run_all(tmp_path)] == names
    finally:
        # restore registry to its import-time state for other tests
        import loop_doctor.checks as checks_mod

        checks_mod._REGISTRY.pop("second", None)


def test_composed_report_carries_single_aggregate_verdict_go(tmp_path: Path) -> None:
    _make_ai_dir(tmp_path / "ai")
    report = Report(checks=run_all(tmp_path))
    assert report.verdict is True


def test_composed_report_carries_single_aggregate_verdict_nogo(tmp_path: Path) -> None:
    report = Report(checks=run_all(tmp_path))
    assert report.verdict is False


def test_composed_report_nogo_when_any_check_fails(tmp_path: Path) -> None:
    _make_ai_dir(tmp_path / "ai")

    def _failing(project_dir: Path) -> Check:
        return Check("failing", Status.FAIL, "boom")

    register("failing", _failing)
    try:
        report = Report(checks=run_all(tmp_path))
        assert report.verdict is False
    finally:
        import loop_doctor.checks as checks_mod

        checks_mod._REGISTRY.pop("failing", None)


def test_run_all_returns_foundation_then_protocol_in_stable_order(
    tmp_path: Path,
) -> None:
    _make_ai_dir(tmp_path / "ai")
    names = [c.name for c in run_all(tmp_path)]
    assert names == ["foundation", "protocol", "prompt", "bash", "run_health", "endpoint", "ci"]
    # stable across repeated calls
    assert [c.name for c in run_all(tmp_path)] == names


def test_composed_report_nogo_when_protocol_fails(tmp_path: Path) -> None:
    # A gate log with a title line but no THE SEED block makes protocol FAIL.
    ai_dir = tmp_path / "ai"
    ai_dir.mkdir(parents=True, exist_ok=True)
    (ai_dir / "cycle-001-loop-doctor-gate.md").write_text(
        chr(10).join(["# cycle-001 gate", "", "no seed block here", ""]),
        encoding="utf-8",
    )
    (ai_dir / "loop-doctor-cycle-runner-prompt.md").write_text(
        "prompt", encoding="utf-8"
    )
    report = Report(checks=run_all(tmp_path))
    protocol = next(c for c in report.checks if c.name == "protocol")
    assert protocol.status is Status.FAIL
    assert report.verdict is False


def test_composed_report_nogo_when_prompt_fails(tmp_path: Path) -> None:
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
    report = Report(checks=run_all(tmp_path))
    prompt = next(c for c in report.checks if c.name == "prompt")
    assert prompt.status is Status.FAIL
    assert report.verdict is False


def test_composed_report_nogo_when_bash_fails(tmp_path: Path) -> None:
    # A .sh driver with a syntax error makes the bash check FAIL -> NO-GO.
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
    (ai_dir / "loop-doctor-cycle-runner-prompt.md").write_text(
        "prompt", encoding="utf-8"
    )
    proj = tmp_path / "proj"
    proj.mkdir(parents=True, exist_ok=True)
    (proj / "run.sh").write_text(
        chr(10).join([
            "#!/usr/bin/env bash",
            "if [ -z $x; then",
            "  echo hi",
            "",
        ]),
        encoding="utf-8",
    )
    report = Report(checks=run_all(tmp_path))
    bash = next(c for c in report.checks if c.name == "bash")
    assert bash.status is Status.FAIL
    assert report.verdict is False


def test_composed_report_nogo_when_run_health_fails(tmp_path: Path) -> None:
    pytest.importorskip("fourseer")
    # A cycles.out with a missing cycle number makes run_health FAIL -> NO-GO.
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
    (ai_dir / "loop-doctor-cycle-runner-prompt.md").write_text(
        "prompt", encoding="utf-8"
    )
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
    report = Report(checks=run_all(tmp_path))
    run_health = next(c for c in report.checks if c.name == "run_health")
    assert run_health.status is Status.FAIL
    assert report.verdict is False


def test_composed_report_nogo_when_endpoint_fails(tmp_path: Path, monkeypatch) -> None:
    # An unreachable endpoint makes the endpoint check FAIL -> NO-GO.
    _make_ai_dir(tmp_path / "ai")
    monkeypatch.setattr(endpoint_mod, "_probe", lambda *a, **k: False)
    report = Report(checks=run_all(tmp_path))
    endpoint = next(c for c in report.checks if c.name == "endpoint")
    assert endpoint.status is Status.FAIL
    assert report.verdict is False
