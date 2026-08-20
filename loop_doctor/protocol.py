"""Protocol check for loop-doctor.

The protocol check verifies that a project's 3-file set is fully present and
that the gate log is well-formed. It reuses :func:`loop_doctor.project.resolve_project`
for resolution (it does not re-implement it) and only inspects the gate log
text for structure. It is dependency-free (no spoke-lint / fourseer).
"""

from __future__ import annotations

import re
from pathlib import Path

from loop_doctor.project import resolve_project
from loop_doctor.report import Check, Status

# A fenced code block opener: a line whose stripped form starts with three
# backticks or three tildes. Backticks are built via chr(96) to keep this
# source free of literal fence characters.
_FENCE_RE = re.compile(r"^\s*(" + chr(96) * 3 + "|~~~)")

# A level-1 title heading: a single "#", a space, then non-whitespace text.
# This deliberately excludes deeper headings such as "## THE SEED".
_TITLE_RE = re.compile(r"^# \S")

# The marker text for the seed block.
_SEED_MARKER = "THE SEED"


def _has_title_line(lines: list[str]) -> bool:
    """Return True if any line is a level-1 ``# ...`` title line.

    A title line is a line whose stripped form is a level-1 heading: it starts
    with ``#`` followed by a space and then non-whitespace text. This excludes
    deeper headings such as ``## THE SEED``, which are not titles.
    """
    for line in lines:
        stripped = line.strip()
        if _TITLE_RE.match(stripped):
            return True
    return False


def _has_seed_block(lines: list[str]) -> bool:
    """Return True if the gate log contains a ``THE SEED`` fenced block.

    A ``THE SEED`` block is a line containing ``THE SEED`` followed (later in
    the log) by a fenced code block opener.
    """
    for i, line in enumerate(lines):
        if _SEED_MARKER in line:
            for j in range(i + 1, len(lines)):
                if _FENCE_RE.match(lines[j]):
                    return True
            return False
    return False


def protocol_check(project_dir: Path) -> Check:
    """The protocol check: the 3-file set is present and the gate log is well-formed.

    Reuses :func:`loop_doctor.project.resolve_project` (does not re-implement
    resolution). PASS when the gate log, runner prompt, and seed ref are all
    located AND the gate log has a ``# ...`` title line AND a ``THE SEED``
    fenced block. FAIL with a detail naming exactly what is missing or
    malformed.
    """
    ai_dir, three = resolve_project(project_dir)
    gate_log = three.gate_log
    runner_prompt = three.runner_prompt

    missing = []
    if gate_log is None:
        missing.append("gate log")
    if runner_prompt is None:
        missing.append("runner prompt")
    if missing:
        return Check("protocol", Status.FAIL, "missing: " + ", ".join(missing))

    # Both the gate log and the runner prompt are located here. mypy cannot
    # narrow ``gate_log`` through the ``missing`` list, so re-check it directly
    # (this branch is unreachable in practice).
    assert gate_log is not None
    try:
        text = gate_log.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return Check("protocol", Status.FAIL, "malformed gate log: unreadable")

    lines = text.splitlines()
    if not _has_title_line(lines):
        return Check("protocol", Status.FAIL, "malformed gate log: no title line")
    if not _has_seed_block(lines):
        return Check("protocol", Status.FAIL, "malformed gate log: no THE SEED block")
    if three.seed_ref is None:
        return Check("protocol", Status.FAIL, "missing: seed ref")

    return Check("protocol", Status.PASS, f"ai dir {ai_dir}")
