"""Endpoint reachability check for loop-doctor.

The endpoint check confirms the LLM backends the build loop depends on are
reachable. It probes a fixed set of endpoints with a plain TCP connect
(stdlib ``socket`` only — no HTTP, no live LLM run) and reports a single
``Check`` named ``endpoint``.

The check is dependency-free. In tests the network seam is isolated by
patching :func:`_probe` (see ``tests/conftest.py``), so the suite stays
deterministic and network-free.
"""

from __future__ import annotations

import socket
from pathlib import Path

from loop_doctor.report import Check, Status

# The LLM endpoints the build loop depends on, as ``(host, port)`` pairs.
# Probed in this stable order; the order is what a FAIL detail lists them in.
_ENDPOINTS: tuple[tuple[str, int], ...] = (
    ("192.168.1.157", 8080),
    ("192.168.1.161", 8081),
)


def _probe(host: str, port: int, timeout: float = 2.0) -> bool:
    """Return ``True`` if a TCP connect to ``host:port`` succeeds in time.

    Uses a blocking ``socket`` connect with a timeout. Any failure — timeout,
    connection refused, network unreachable, or DNS failure — returns ``False``.
    Stdlib only: this is a plain TCP connect, not an HTTP request or a live LLM
    run.
    """
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return True
    except OSError:
        return False


def endpoint_check(project_dir: Path) -> Check:
    """The endpoint check: every LLM endpoint is reachable.

    Probes each endpoint in :data:`_ENDPOINTS` via :func:`_probe`. PASS with
    ``"<n> endpoint(s) reachable"`` when every endpoint is reachable; FAIL with
    a detail naming each unreachable endpoint as ``host:port``.
    """
    unreachable = [f"{host}:{port}" for host, port in _ENDPOINTS if not _probe(host, port)]
    if unreachable:
        return Check("endpoint", Status.FAIL, "unreachable: " + ", ".join(unreachable))
    return Check("endpoint", Status.PASS, f"{len(_ENDPOINTS)} endpoint(s) reachable")
