"""Tests for loop_doctor.report: stability, round-trip, verdict/exit mapping."""

from __future__ import annotations

import json

from loop_doctor.report import Check, Report, Status, exit_code, render_json, render_text


def _sample_report() -> Report:
    return Report(
        checks=[
            Check("foundation", Status.PASS, "ai dir resolved"),
            Check("protocol", Status.WARN, "seed ref missing"),
            Check("prompt-lint", Status.SKIP, "optional dep absent"),
        ]
    )


def test_render_text_is_byte_stable() -> None:
    report = _sample_report()
    assert render_text(report) == render_text(report)


def test_render_json_is_byte_stable() -> None:
    report = _sample_report()
    assert render_json(report) == render_json(report)


def test_render_text_preserves_insertion_order_and_verdict_first() -> None:
    report = _sample_report()
    text = render_text(report)
    lines = text.splitlines()
    assert lines[0] == "verdict: GO"
    # insertion order preserved
    assert "foundation" in lines[1]
    assert "protocol" in lines[2]
    assert "prompt-lint" in lines[3]


def test_render_json_round_trips_verdict_and_checks() -> None:
    report = _sample_report()
    data = json.loads(render_json(report))
    assert data["verdict"] is True
    assert [c["name"] for c in data["checks"]] == ["foundation", "protocol", "prompt-lint"]
    assert data["checks"][0]["status"] == "pass"
    assert data["checks"][1]["status"] == "warn"
    assert data["checks"][2]["status"] == "skip"
    assert data["checks"][0]["detail"] == "ai dir resolved"


def test_verdict_false_when_any_fail() -> None:
    report = Report(checks=[Check("a", Status.PASS), Check("b", Status.FAIL)])
    assert report.verdict is False
    assert report.go is False


def test_verdict_true_when_only_pass_warn_skip() -> None:
    report = Report(
        checks=[Check("a", Status.PASS), Check("b", Status.WARN), Check("c", Status.SKIP)]
    )
    assert report.verdict is True
    assert report.go is True


def test_verdict_true_when_empty() -> None:
    assert Report(checks=[]).verdict is True


def test_exit_code_maps_go_to_zero_and_nogo_to_one() -> None:
    assert exit_code(Report(checks=[Check("a", Status.PASS)])) == 0
    assert exit_code(Report(checks=[Check("a", Status.FAIL)])) == 1
    # WARN/SKIP do not block
    assert exit_code(Report(checks=[Check("a", Status.WARN), Check("b", Status.SKIP)])) == 0
