"""Prompt lint check for loop-doctor.

The prompt check validates the runner prompt's spoke invocations against the
argparse signatures of the referenced spoke scripts, using the optional
``spoke_lint`` library. It reuses :func:`loop_doctor.project.resolve_project`
to locate the runner prompt (it does not re-implement resolution).

The check is dependency-free except for the optional ``spoke_lint`` import,
which is guarded with ``try/except ImportError``: when ``spoke_lint`` is not
installed the check returns ``Status.SKIP`` (non-blocking) rather than failing.

Only *invocation* findings are considered (``missing_script``,
``unknown_flag``, ``missing_required``). Gate-command findings
(``missing_tool``) are deliberately ignored: a real runner prompt is
prose-heavy, and the gate-command stage of ``spoke_lint`` treats prose lines,
fenced blocks, and numbered lists as "gate tools", producing false positives
that are unrelated to whether the spoke invocations are valid.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from loop_doctor.project import resolve_project
from loop_doctor.report import Check, Status

# Finding kinds that describe a problem with a spoke *invocation* (as opposed
# to a gate-command tool). Only these are considered by the prompt check.
_INVOCATION_KINDS = frozenset({"missing_script", "unknown_flag", "missing_required"})

# A directory reference ending in "/spokes" (e.g. "~/Research/four/examples/spokes").
_SPOKES_DIR_RE = re.compile(r"(\S*/spokes)")

# Default spokes dir when the prompt does not reference a "/spokes" directory.
_DEFAULT_SPOKES_DIR = Path("spokes")


def _resolve_spokes_dir(text: str) -> Path:
    """Return the directory the prompt's spoke invocations point at.

    Finds the first path reference ending in ``/spokes`` in the prompt text and
    returns it (with ``~`` expanded). When no such reference is present, returns
    a default ``spokes`` directory.
    """
    match = _SPOKES_DIR_RE.search(text)
    if match is None:
        return _DEFAULT_SPOKES_DIR
    return Path(match.group(1)).expanduser()


def _invocation_findings(findings: list[Any]) -> list[Any]:
    """Return only the invocation findings from a list of spoke_lint findings.

    Gate-command findings (``missing_tool``) are dropped so that prose-heavy
    prompts are not penalised for lines that are not spoke invocations.
    """
    return [f for f in findings if f.kind in _INVOCATION_KINDS]


def _format_findings(findings: list[Any]) -> str:
    """Render invocation findings as a stable, semicolon-separated detail string."""
    return "; ".join(f"{f.kind}: {f.flag}" for f in findings)


def prompt_check(project_dir: Path) -> Check:
    """The prompt check: the runner prompt's spoke invocations are valid.

    Reuses :func:`loop_doctor.project.resolve_project` (does not re-implement
    resolution). FAIL with "missing: runner prompt" when the runner prompt is
    not located. SKIP (non-blocking) with "spoke-lint not installed" when
    ``spoke_lint`` is not importable. Otherwise PASS when the prompt has no
    invocation findings; FAIL with a detail naming the findings.
    """
    ai_dir, three = resolve_project(project_dir)
    runner_prompt = three.runner_prompt
    if runner_prompt is None:
        return Check("prompt", Status.FAIL, "missing: runner prompt")

    try:
        import spoke_lint
    except ImportError:
        return Check("prompt", Status.SKIP, "spoke-lint not installed")

    try:
        text = runner_prompt.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return Check("prompt", Status.FAIL, "unreadable runner prompt")

    spokes_dir = _resolve_spokes_dir(text)
    findings = _invocation_findings(spoke_lint.diff_prompt(text, spokes_dir))
    if not findings:
        return Check("prompt", Status.PASS, f"ai dir {ai_dir}")
    return Check("prompt", Status.FAIL, _format_findings(findings))
