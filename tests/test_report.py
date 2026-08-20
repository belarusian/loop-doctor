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


def test_add_grows_report_and_verdict_tracks_it() -> None:
    report = Report()
    assert report.checks == []
    assert report.verdict is True
    report.add(Check("a", Status.PASS))
    assert len(report.checks) == 1
    assert report.verdict is True
    report.add(Check("b", Status.FAIL))
    assert len(report.checks) == 2
    assert report.verdict is False


def test_summary_counts_are_correct_and_stable() -> None:
    report = Report(
        checks=[
            Check("a", Status.PASS),
            Check("b", Status.FAIL),
            Check("c", Status.WARN),
            Check("d", Status.SKIP),
            Check("e", Status.PASS),
        ]
    )
    assert report.summary() == "pass=2 fail=1 warn=1 skip=1"
    # stable across repeated calls
    assert report.summary() == report.summary()


def test_summary_is_independent_of_insertion_order() -> None:
    r1 = Report(checks=[Check("a", Status.PASS), Check("b", Status.FAIL)])
    r2 = Report(checks=[Check("b", Status.FAIL), Check("a", Status.PASS)])
    assert r1.summary() == r2.summary()
    assert r1.summary() == "pass=1 fail=1 warn=0 skip=0"


def test_summary_empty_report() -> None:
    assert Report().summary() == "pass=0 fail=0 warn=0 skip=0"


def test_render_text_byte_stable_for_sample_report() -> None:
    report = _sample_report()
    expected = (
        "verdict: GO\n"
        "PASS  foundation — ai dir resolved\n"
        "WARN  protocol — seed ref missing\n"
        "SKIP  prompt-lint — optional dep absent\n"
    )
    assert render_text(report) == expected


def test_render_json_byte_stable_for_sample_report() -> None:
    report = _sample_report()
    expected = (
        "{\n"
        '  "checks": [\n'
        "    {\n"
        '      "detail": "ai dir resolved",\n'
        '      "name": "foundation",\n'
        '      "status": "pass"\n'
        "    },\n"
        "    {\n"
        '      "detail": "seed ref missing",\n'
        '      "name": "protocol",\n'
        '      "status": "warn"\n'
        "    },\n"
        "    {\n"
        '      "detail": "optional dep absent",\n'
        '      "name": "prompt-lint",\n'
        '      "status": "skip"\n'
        "    }\n"
        "  ],\n"
        '  "verdict": true\n'
        "}\n"
    )
    assert render_json(report) == expected
