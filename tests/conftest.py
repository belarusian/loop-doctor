"""Shared pytest fixtures for the loop-doctor test suite.

The endpoint check probes real network endpoints. To keep the whole suite
deterministic and network-free, an autouse fixture patches
``loop_doctor.endpoint._probe`` to return ``True`` (every endpoint reachable)
for every test. Tests that need a specific probe outcome (e.g. the endpoint
FAIL cases) override the seam with ``monkeypatch`` on top of this default.
"""

from __future__ import annotations

from collections.abc import Iterator
from unittest import mock

import pytest

import loop_doctor.endpoint as endpoint


@pytest.fixture(autouse=True)
def _probe_all_reachable() -> Iterator[None]:
    """Patch ``endpoint._probe`` to report every endpoint reachable.

    Yields so the patch is active for the whole test and restored afterwards.
    Tests may override ``endpoint._probe`` via ``monkeypatch`` to simulate
    unreachable endpoints; that override is applied on top of this default and
    restored before this fixture tears down.
    """
    with mock.patch.object(endpoint, "_probe", return_value=True):
        yield
