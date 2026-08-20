"""Tests for loop_doctor.endpoint: the endpoint reachability check.

All tests are deterministic and network-free. The autouse fixture in
``tests/conftest.py`` patches ``endpoint._probe`` to ``True`` by default; the
FAIL cases override that seam with ``monkeypatch`` to simulate unreachable
endpoints.
"""

from __future__ import annotations

from pathlib import Path

from loop_doctor.endpoint import _ENDPOINTS, endpoint_check
from loop_doctor.report import Status


def test_endpoint_passes_when_all_reachable(tmp_path: Path) -> None:
    # Default autouse fixture: _probe -> True for every endpoint.
    check = endpoint_check(tmp_path)
    assert check.name == "endpoint"
    assert check.status is Status.PASS
    assert check.detail == f"{len(_ENDPOINTS)} endpoint(s) reachable"


def test_endpoint_fails_naming_one_unreachable(tmp_path: Path, monkeypatch) -> None:
    # The first endpoint is down, the second is up -> FAIL naming only the first.
    def _fake_probe(host: str, port: int, timeout: float = 2.0) -> bool:
        return (host, port) != _ENDPOINTS[0]

    monkeypatch.setattr("loop_doctor.endpoint._probe", _fake_probe)
    check = endpoint_check(tmp_path)
    assert check.status is Status.FAIL
    assert f"{_ENDPOINTS[0][0]}:{_ENDPOINTS[0][1]}" in check.detail
    assert f"{_ENDPOINTS[1][0]}:{_ENDPOINTS[1][1]}" not in check.detail


def test_endpoint_fails_when_both_down(tmp_path: Path, monkeypatch) -> None:
    # Every endpoint is down -> FAIL naming both.
    monkeypatch.setattr("loop_doctor.endpoint._probe", lambda *a, **k: False)
    check = endpoint_check(tmp_path)
    assert check.status is Status.FAIL
    assert f"{_ENDPOINTS[0][0]}:{_ENDPOINTS[0][1]}" in check.detail
    assert f"{_ENDPOINTS[1][0]}:{_ENDPOINTS[1][1]}" in check.detail


def test_endpoint_probe_override_via_monkeypatch(tmp_path: Path, monkeypatch) -> None:
    # A custom probe that reports exactly one reachable endpoint drives the
    # outcome: the reachable count and the named unreachable endpoint both
    # reflect the override, proving the check routes through the _probe seam.
    def _fake_probe(host: str, port: int, timeout: float = 2.0) -> bool:
        return (host, port) == _ENDPOINTS[1]

    monkeypatch.setattr("loop_doctor.endpoint._probe", _fake_probe)
    check = endpoint_check(tmp_path)
    assert check.status is Status.FAIL
    assert f"{_ENDPOINTS[0][0]}:{_ENDPOINTS[0][1]}" in check.detail
    assert f"{_ENDPOINTS[1][0]}:{_ENDPOINTS[1][1]}" not in check.detail
