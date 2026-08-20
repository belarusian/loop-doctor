"""Tests for loop_doctor.checks: registry composition and aggregate verdict."""

from __future__ import annotations

from pathlib import Path

from loop_doctor.checks import register, run_all
from loop_doctor.report import Check, Report, Status


def _make_ai_dir(ai_dir: Path) -> None:
    ai_dir.mkdir(parents=True, exist_ok=True)
    (ai_dir / "cycle-001-loop-doctor-gate.md").write_text("gate", encoding="utf-8")
    (ai_dir / "loop-doctor-cycle-runner-prompt.md").write_text("prompt", encoding="utf-8")


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
        # foundation was registered at import time, so it comes first.
        assert names == ["foundation", "second"]
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
