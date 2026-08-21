"""Tests for loop_doctor.ci: the GitHub Actions CI check.

Table-driven, mocked (``patch.object`` on ``loop_doctor.ci._run``), and
network-free. Each case drives ``_run`` to return canned
``subprocess.CompletedProcess`` objects for the git/gh commands in the order
``ci_check`` issues them.
"""

from __future__ import annotations

import json
import subprocess
from pathlib import Path
from unittest import mock

import pytest

import loop_doctor.ci as ci_mod
from loop_doctor.ci import ci_check
from loop_doctor.report import Report, Status

SHA = "abcdef0123456789abcdef0123456789abcdef01"
SHORT = SHA[:7]


def _cp(rc: int, stdout: str = "", stderr: str = "") -> subprocess.CompletedProcess:
    """Build a canned CompletedProcess."""
    return subprocess.CompletedProcess(args=[], returncode=rc, stdout=stdout, stderr=stderr)


def _check_runs_payload(runs: list[dict]) -> str:
    return json.dumps({"total_count": len(runs), "check_runs": runs})


def _run_side_effect(*responses: subprocess.CompletedProcess):
    """Return a side_effect callable that yields responses in order."""
    it = iter(responses)
    return lambda cmd: next(it)


def test_ci_green_passes(tmp_path: Path) -> None:
    # git inside work tree, origin URL, fetch ok, rev-parse ok, gh green.
    responses = [
        _cp(0, stdout="true\n"),
        _cp(0, stdout="https://github.com/belarusian/loop-doctor.git\n"),
        _cp(0),
        _cp(0, stdout=SHA + "\n"),
        _cp(0, stdout=_check_runs_payload([
            {"name": "test", "status": "completed", "conclusion": "success"},
            {"name": "lint", "status": "completed", "conclusion": "success"},
        ])),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.name == "ci"
    assert check.status is Status.PASS
    assert f"CI green at {SHORT}" in check.detail
    report = Report(checks=[check])
    assert report.verdict is True


def test_ci_red_fails(tmp_path: Path) -> None:
    responses = [
        _cp(0, stdout="true\n"),
        _cp(0, stdout="git@github.com:belarusian/loop-doctor.git\n"),
        _cp(0),
        _cp(0, stdout=SHA + "\n"),
        _cp(0, stdout=_check_runs_payload([
            {"name": "test", "status": "completed", "conclusion": "success"},
            {"name": "lint", "status": "completed", "conclusion": "failure"},
        ])),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.status is Status.FAIL
    assert f"CI red at {SHORT}" in check.detail
    assert "lint" in check.detail
    report = Report(checks=[check])
    assert report.verdict is False


def test_ci_in_progress_fails(tmp_path: Path) -> None:
    responses = [
        _cp(0, stdout="true\n"),
        _cp(0, stdout="https://github.com/belarusian/loop-doctor\n"),
        _cp(0),
        _cp(0, stdout=SHA + "\n"),
        _cp(0, stdout=_check_runs_payload([
            {"name": "test", "status": "completed", "conclusion": "success"},
            {"name": "lint", "status": "in_progress", "conclusion": None},
        ])),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.status is Status.FAIL
    assert f"CI in progress for {SHORT}" in check.detail
    assert "1/2 completed" in check.detail


def test_ci_zero_check_runs_skips(tmp_path: Path) -> None:
    responses = [
        _cp(0, stdout="true\n"),
        _cp(0, stdout="https://github.com/belarusian/loop-doctor.git\n"),
        _cp(0),
        _cp(0, stdout=SHA + "\n"),
        _cp(0, stdout=_check_runs_payload([])),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.status is Status.SKIP
    assert f"no check runs for {SHORT}" in check.detail


def test_ci_not_a_repo_skips(tmp_path: Path) -> None:
    # rev-parse --is-inside-work-tree fails.
    responses = [
        _cp(128, stderr="fatal: not a git repository\n"),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.status is Status.SKIP
    assert "not a git repo with origin" in check.detail


def test_ci_no_origin_skips(tmp_path: Path) -> None:
    # inside work tree, but no origin remote.
    responses = [
        _cp(0, stdout="true\n"),
        _cp(128, stderr="fatal: no remote named origin\n"),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.status is Status.SKIP
    assert "not a git repo with origin" in check.detail


def test_ci_non_github_remote_skips(tmp_path: Path) -> None:
    responses = [
        _cp(0, stdout="true\n"),
        _cp(0, stdout="https://gitlab.com/belarusian/loop-doctor.git\n"),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.status is Status.SKIP
    assert "non-GitHub remote" in check.detail


def test_ci_gh_missing_skips(tmp_path: Path) -> None:
    # gh binary missing -> _run normalizes to returncode 127.
    responses = [
        _cp(0, stdout="true\n"),
        _cp(0, stdout="https://github.com/belarusian/loop-doctor.git\n"),
        _cp(0),
        _cp(0, stdout=SHA + "\n"),
        _cp(127, stderr="gh: command not found"),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.status is Status.SKIP
    assert "gh check-runs failed" in check.detail


def test_ci_gh_invalid_json_skips(tmp_path: Path) -> None:
    responses = [
        _cp(0, stdout="true\n"),
        _cp(0, stdout="https://github.com/belarusian/loop-doctor.git\n"),
        _cp(0),
        _cp(0, stdout=SHA + "\n"),
        _cp(0, stdout="not json at all"),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.status is Status.SKIP
    assert "invalid check-runs JSON" in check.detail


def test_ci_fetch_fails_but_local_ref_resolves(tmp_path: Path) -> None:
    # fetch fails, but rev-parse origin/main still resolves -> proceed, note it.
    responses = [
        _cp(0, stdout="true\n"),
        _cp(0, stdout="https://github.com/belarusian/loop-doctor.git\n"),
        _cp(128, stderr="fatal: could not read from remote repository\n"),
        _cp(0, stdout=SHA + "\n"),
        _cp(0, stdout=_check_runs_payload([
            {"name": "test", "status": "completed", "conclusion": "success"},
        ])),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.status is Status.PASS
    assert f"CI green at {SHORT}" in check.detail
    assert "using local origin/main ref" in check.detail


def test_ci_cannot_resolve_origin_main_skips(tmp_path: Path) -> None:
    # fetch ok, but rev-parse origin/main fails -> SKIP.
    responses = [
        _cp(0, stdout="true\n"),
        _cp(0, stdout="https://github.com/belarusian/loop-doctor.git\n"),
        _cp(0),
        _cp(128, stderr="fatal: ambiguous argument origin/main\n"),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.status is Status.SKIP
    assert "cannot resolve origin/main" in check.detail


def test_ci_skipped_conclusion_is_green(tmp_path: Path) -> None:
    # A skipped conclusion is non-blocking -> PASS.
    responses = [
        _cp(0, stdout="true\n"),
        _cp(0, stdout="https://github.com/belarusian/loop-doctor.git\n"),
        _cp(0),
        _cp(0, stdout=SHA + "\n"),
        _cp(0, stdout=_check_runs_payload([
            {"name": "test", "status": "completed", "conclusion": "success"},
            {"name": "lint", "status": "completed", "conclusion": "skipped"},
        ])),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.status is Status.PASS


def test_ci_cancelled_conclusion_fails(tmp_path: Path) -> None:
    responses = [
        _cp(0, stdout="true\n"),
        _cp(0, stdout="https://github.com/belarusian/loop-doctor.git\n"),
        _cp(0),
        _cp(0, stdout=SHA + "\n"),
        _cp(0, stdout=_check_runs_payload([
            {"name": "test", "status": "completed", "conclusion": "cancelled"},
        ])),
    ]
    with mock.patch.object(ci_mod, "_run", side_effect=_run_side_effect(*responses)):
        check = ci_check(tmp_path)
    assert check.status is Status.FAIL
    assert "test" in check.detail
