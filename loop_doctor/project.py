"""Directory resolution and the 3-file set for loop-doctor.

The four-pipeline layout keeps, per project, a ``proj`` checkout and a sibling
``ai`` dir (one level up) holding the gate log, runner prompt, briefings, and
trajectories. This module resolves the ``ai`` dir from either the ``proj`` dir
or its parent, and locates the 3-file set:

- **gate log** - the append-only markdown log (``cycle-*-*-gate.md``).
- **runner prompt** - the inner spoke prompt (``*-runner-prompt.md``).
- **seed reference** - the read-only seed path named in the gate log
  ``THE SEED`` fenced block (parsed, never hardcoded).
"""

from __future__ import annotations

import fnmatch
import re
from dataclasses import dataclass
from pathlib import Path

_SEED_LINE_RE = re.compile("THE SEED")
_FENCE_RE = re.compile("^" + chr(92) + "s*(" + chr(96) * 3 + "|~~~)")


@dataclass(frozen=True)
class ThreeFiles:
    """The 3-file set for a project. Any field may be ``None`` if absent."""

    gate_log: Path | None
    runner_prompt: Path | None
    seed_ref: Path | None


def resolve_ai_dir(project_dir: Path) -> Path:
    """Return the sibling ``ai`` dir for a project.

    Accepts either the ``proj`` dir itself or its parent. If ``project_dir``
    is named ``proj``, the ``ai`` dir is its sibling (``project_dir.parent /
    "ai"``); otherwise ``project_dir`` is treated as the parent and the ``ai``
    dir is ``project_dir / "ai"``. The returned path need not exist.
    """
    project_dir = Path(project_dir)
    if project_dir.name == "proj":
        return project_dir.parent / "ai"
    return project_dir / "ai"


def _first_match(ai_dir: Path, pattern: str) -> Path | None:
    """Return the first file in ``ai_dir`` matching ``pattern`` (sorted)."""
    if not ai_dir.is_dir():
        return None
    matches = sorted(
        p for p in ai_dir.iterdir() if p.is_file() and fnmatch.fnmatch(p.name, pattern)
    )
    return matches[0] if matches else None


def _parse_seed_ref(gate_log: Path) -> Path | None:
    """Parse the seed path from the ``THE SEED`` fenced block in a gate log.

    Finds the first line containing ``THE SEED``, then the next fenced code
    block, and returns the first non-empty line inside it as a ``Path``.
    Returns ``None`` if the block is absent or unparseable.
    """
    try:
        text = gate_log.read_text(encoding="utf-8")
    except (OSError, UnicodeDecodeError):
        return None

    lines = text.splitlines()
    seed_idx = None
    for i, line in enumerate(lines):
        if _SEED_LINE_RE.search(line):
            seed_idx = i
            break
    if seed_idx is None:
        return None

    i = seed_idx + 1
    while i < len(lines) and not _FENCE_RE.match(lines[i]):
        i += 1
    if i >= len(lines):
        return None

    i += 1
    while i < len(lines) and not _FENCE_RE.match(lines[i]):
        stripped = lines[i].strip()
        if stripped:
            return Path(stripped)
        i += 1
    return None


def locate_three_files(ai_dir: Path) -> ThreeFiles:
    """Locate the 3-file set in ``ai_dir``.

    ``gate_log`` is the first ``cycle-*-*-gate.md`` file (sorted,
    deterministic); ``runner_prompt`` is the first ``*-runner-prompt.md`` file;
    ``seed_ref`` is parsed from the gate log ``THE SEED`` block. Any of the
    three may be ``None`` if absent or unparseable.
    """
    gate_log = _first_match(ai_dir, "cycle-*-*-gate.md")
    runner_prompt = _first_match(ai_dir, "*-runner-prompt.md")
    seed_ref = _parse_seed_ref(gate_log) if gate_log is not None else None
    return ThreeFiles(gate_log=gate_log, runner_prompt=runner_prompt, seed_ref=seed_ref)


def resolve_project(project_dir: Path) -> tuple[Path, ThreeFiles]:
    """Convenience: resolve the ``ai`` dir and its 3-file set together."""
    ai_dir = resolve_ai_dir(project_dir)
    return ai_dir, locate_three_files(ai_dir)
