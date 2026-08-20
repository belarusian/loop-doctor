"""Tests for loop_doctor.endpoint: the endpoint reachability check.

All tests are deterministic and network-free. The autouse fixture in
``tests/conftest.py`` patches ``endpoint._probe`` to ``True`` by default; the
FAIL cases override that seam with ``monkeypatch`` to simulate unreachable
endpoints.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from loop_doctor.endpoint import _ENDPOINTS, endpoint_check
from loop_doctor.report import Status

# The exact endpoint set the check probes, in stable order.
EXPECTED_ENDPOINTS = (("192.168.1.157", 8080), ("192.168.1.161", 8081))


def test_endpoint_list_is_exactly_the_two_llm_endpoints() -> None:
    # The endpoint set is pinned exactly: two (host, port) pairs in stable order.
    assert _ENDPOINTS == EXPECTED_ENDPOINTS
    assert len(_ENDPOINTS) == 2


def test_endpoint_passes_when_all_reachable(tmp_path: Path) -> None:
    # Default autouse fixture: _probe -> True for every endpoint.
    check = endpoint_check(tmp_path)
    assert check.name == "endpoint"
    assert check.status is Status.PASS
    assert check.detail == f"{len(_ENDPOINTS)} endpoint(s) reachable"


def test_endpoint_pass_detail_is_exact() -> None:
    # The PASS detail string is pinned exactly (not just a substring).
    check = endpoint_check(Path("/nonexistent/dir"))
    assert check.detail == "2 endpoint(s) reachable"


@pytest.mark.parametrize("down_index", [0, 1])
def test_endpoint_fails_naming_one_unreachable(
    tmp_path: Path, monkeypatch, down_index: int,
) -> None:
    # Exactly one endpoint is down (parametrized over which); the detail names
    # only the down endpoint as host:port and omits the up one.
    down = _ENDPOINTS[down_index]
    up = _ENDPOINTS[1 - down_index]

    def _fake_probe(host: str, port: int, timeout: float = 2.0) -> bool:
        return (host, port) != down

    monkeypatch.setattr("loop_doctor.endpoint._probe", _fake_probe)
    check = endpoint_check(tmp_path)
    assert check.status is Status.FAIL
    assert check.detail == f"unreachable: {down[0]}:{down[1]}"
    assert f"{up[0]}:{up[1]}" not in check.detail


def test_endpoint_fails_when_both_down(tmp_path: Path, monkeypatch) -> None:
    # Every endpoint is down -> FAIL naming both, in stable order.
    monkeypatch.setattr("loop_doctor.endpoint._probe", lambda *a, **k: False)
    check = endpoint_check(tmp_path)
    assert check.status is Status.FAIL
    assert check.detail == "unreachable: 192.168.1.157:8080, 192.168.1.161:8081"


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


def test_endpoint_check_is_independent_of_project_dir() -> None:
    # The endpoint check never reads the filesystem: a nonexistent project dir
    # still yields the same PASS as a real dir under the default (all-up) probe.
    assert endpoint_check(Path("/does/not/exist")).status is Status.PASS
    assert endpoint_check(Path("/does/not/exist")).detail == "2 endpoint(s) reachable"
