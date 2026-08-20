"""Deterministic report model and renderers for loop-doctor.

This module defines the single source of truth for a check result, the
go/no-go verdict, and the stable text/JSON renderers. It has no external
dependencies and produces byte-stable output: no timestamps, no hostnames,
no reliance on dict/set iteration order.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Status(str, Enum):
    """Outcome of a single check.

    ``PASS``/``FAIL`` are the blocking states. ``WARN`` and ``SKIP`` are
    non-blocking: they surface information but never flip the verdict.
    """

    PASS = "pass"
    FAIL = "fail"
    WARN = "warn"
    SKIP = "skip"


@dataclass(frozen=True)
class Check:
    """A single named check with a status and an optional detail string."""

    name: str
    status: Status
    detail: str = ""


@dataclass
class Report:
    """An ordered collection of checks plus a derived go/no-go verdict.

    The verdict is ``True`` (go) if and only if no check has status ``FAIL``.
    ``WARN`` and ``SKIP`` do not block. Checks are rendered in insertion order
    (the order they were appended), which is deterministic.
    """

    checks: list[Check] = field(default_factory=list)

    @property
    def verdict(self) -> bool:
        """Go if there is no FAIL among the checks."""
        return all(c.status is not Status.FAIL for c in self.checks)

    @property
    def go(self) -> bool:
        """Alias of :attr:`verdict`."""
        return self.verdict


def render_text(report: Report) -> str:
    """Render a stable, human-readable text report.

    The verdict line comes first, followed by one line per check in insertion
    order. Output is byte-stable for a given report.
    """
    verdict = "GO" if report.verdict else "NO-GO"
    lines = [f"verdict: {verdict}"]
    for check in report.checks:
        line = f"{check.status.value.upper():5} {check.name}"
        if check.detail:
            line += f" — {check.detail}"
        lines.append(line)
    return "\n".join(lines) + "\n"


def render_json(report: Report) -> str:
    """Render a stable JSON report.

    Uses ``sort_keys=True`` and ``indent=2``. No timestamps or hostnames are
    included, so the output is fully deterministic for a given report.
    """
    payload: dict[str, Any] = {
        "verdict": report.verdict,
        "checks": [
            {"name": c.name, "status": c.status.value, "detail": c.detail}
            for c in report.checks
        ],
    }
    return json.dumps(payload, sort_keys=True, indent=2) + "\n"


def exit_code(report: Report) -> int:
    """Map a report to a process exit code: 0 for go, 1 for no-go."""
    return 0 if report.verdict else 1
