"""Tests for loop_doctor.protocol: the protocol check PASS/FAIL cases.

All tests are deterministic and network-free. A well-formed gate log has a
level-1 ``# ...`` title line and a ``## THE SEED`` fenced block.
"""

from __future__ import annotations

from pathlib import Path

from loop_doctor.protocol import protocol_check
from loop_doctor.report import Status

FENCE = '`' * 3
NL = '\n'


def _wellformed_gate() -> str:
    """A well-formed gate log: a level-1 title line and a THE SEED block."""
    return NL.join([
        "# cycle-001 gate",
        "",
        "## THE SEED",
        "",
        FENCE,
        "/home/sasha/Research/four",
        FENCE,
        "",
        "## notes",
        "append-only log",
    ])


def _make_ai_dir(
    ai_dir: Path,
    *,
    gate: bool = True,
    prompt: bool = True,
    gate_text: str | None = None,
) -> None:
    """Build a 3-file set under ``ai_dir`` with optional toggles."""
    ai_dir.mkdir(parents=True, exist_ok=True)
    if gate:
        text = gate_text if gate_text is not None else _wellformed_gate()
        (ai_dir / "cycle-001-loop-doctor-gate.md").write_text(text, encoding="utf-8")
    if prompt:
        (ai_dir / "loop-doctor-cycle-runner-prompt.md").write_text(
            NL.join(["# runner prompt", ""]), encoding="utf-8"
        )


def test_protocol_pass_on_wellformed_three_file_set(tmp_path: Path) -> None:
    _make_ai_dir(tmp_path / "ai")
    check = protocol_check(tmp_path)
    assert check.name == "protocol"
    assert check.status is Status.PASS


def test_protocol_fails_when_gate_log_missing(tmp_path: Path) -> None:
    _make_ai_dir(tmp_path / "ai", gate=False)
    check = protocol_check(tmp_path)
    assert check.status is Status.FAIL
    assert "gate log" in check.detail


def test_protocol_fails_when_runner_prompt_missing(tmp_path: Path) -> None:
    _make_ai_dir(tmp_path / "ai", prompt=False)
    check = protocol_check(tmp_path)
    assert check.status is Status.FAIL
    assert "runner prompt" in check.detail


def test_protocol_fails_when_seed_block_absent(tmp_path: Path) -> None:
    # A gate log with a title line but no THE SEED fenced block.
    gate = NL.join(["# cycle-001 gate", "", "no seed block here", ""])
    _make_ai_dir(tmp_path / "ai", gate_text=gate)
    check = protocol_check(tmp_path)
    assert check.status is Status.FAIL
    assert "THE SEED" in check.detail


def test_protocol_fails_when_gate_log_lacks_title_line(tmp_path: Path) -> None:
    # A gate log with a THE SEED block but no level-1 title line.
    gate = NL.join([
        "## THE SEED",
        "",
        FENCE,
        "/home/sasha/Research/four",
        FENCE,
        "",
    ])
    _make_ai_dir(tmp_path / "ai", gate_text=gate)
    check = protocol_check(tmp_path)
    assert check.status is Status.FAIL
    assert "title line" in check.detail


def test_protocol_fails_when_seed_ref_unresolvable(tmp_path: Path) -> None:
    # A gate log with a title line and a THE SEED marker, but the fenced block
    # is empty so the seed ref cannot be resolved.
    gate = NL.join([
        "# cycle-001 gate",
        "",
        "## THE SEED",
        "",
        FENCE,
        FENCE,
        "",
    ])
    _make_ai_dir(tmp_path / "ai", gate_text=gate)
    check = protocol_check(tmp_path)
    assert check.status is Status.FAIL
    assert "seed ref" in check.detail
