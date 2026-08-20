"""Tests for loop_doctor.protocol: the protocol check PASS/FAIL cases.

All tests are deterministic and network-free. A well-formed gate log has a
level-1 ``# ...`` title line and a ``## THE SEED`` fenced block.
"""

from __future__ import annotations

from pathlib import Path

from loop_doctor.protocol import _has_seed_block, _has_title_line, protocol_check
from loop_doctor.report import Status

FENCE = '`' * 3
TILDE_FENCE = '~~~'
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


def test_protocol_pass_detail_is_exact(tmp_path: Path) -> None:
    # The PASS detail is pinned exactly: "ai dir <resolved ai dir>".
    _make_ai_dir(tmp_path / "ai")
    check = protocol_check(tmp_path)
    assert check.detail == f"ai dir {tmp_path / 'ai'}"


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


def test_protocol_fails_when_both_missing_lists_both(tmp_path: Path) -> None:
    # Both the gate log and the runner prompt are absent -> the detail names
    # both, in the fixed order (gate log first, then runner prompt).
    _make_ai_dir(tmp_path / "ai", gate=False, prompt=False)
    check = protocol_check(tmp_path)
    assert check.status is Status.FAIL
    assert check.detail == "missing: gate log, runner prompt"


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


def test_protocol_fails_on_empty_gate_log(tmp_path: Path) -> None:
    # An empty gate log has no title line -> FAIL naming the title line.
    _make_ai_dir(tmp_path / "ai", gate_text="")
    check = protocol_check(tmp_path)
    assert check.status is Status.FAIL
    assert "title line" in check.detail


def test_protocol_passes_with_tilde_fence(tmp_path: Path) -> None:
    # A THE SEED block fenced with ~~~ (not backticks) is still well-formed.
    gate = NL.join([
        "# cycle-001 gate",
        "",
        "## THE SEED",
        "",
        TILDE_FENCE,
        "/home/sasha/Research/four",
        TILDE_FENCE,
        "",
    ])
    _make_ai_dir(tmp_path / "ai", gate_text=gate)
    check = protocol_check(tmp_path)
    assert check.status is Status.PASS


def test_protocol_fails_when_seed_marker_has_no_following_fence(tmp_path: Path) -> None:
    # A THE SEED marker with no fenced block after it -> no THE SEED block.
    gate = NL.join([
        "# cycle-001 gate",
        "",
        "## THE SEED",
        "",
        "the seed is here but not fenced",
        "",
    ])
    _make_ai_dir(tmp_path / "ai", gate_text=gate)
    check = protocol_check(tmp_path)
    assert check.status is Status.FAIL
    assert "THE SEED" in check.detail


def test_has_title_line_accepts_level_one_heading() -> None:
    assert _has_title_line(["# cycle-001 gate"]) is True
    assert _has_title_line(["   # indented title"]) is True


def test_has_title_line_rejects_deeper_headings() -> None:
    # A level-2 heading is not a title line.
    assert _has_title_line(["## THE SEED"]) is False
    assert _has_title_line(["### deep"]) is False


def test_has_title_line_rejects_bare_hash() -> None:
    # A bare "#" with no following non-whitespace is not a title line.
    assert _has_title_line(["#"]) is False
    assert _has_title_line(["# "]) is False


def test_has_title_line_false_when_no_lines() -> None:
    assert _has_title_line([]) is False


def test_has_seed_block_true_when_marker_then_fence() -> None:
    lines = ["## THE SEED", "", FENCE, "/home/sasha/Research/four", FENCE]
    assert _has_seed_block(lines) is True


def test_has_seed_block_true_with_tilde_fence() -> None:
    lines = ["## THE SEED", "", TILDE_FENCE, "/home/sasha/Research/four", TILDE_FENCE]
    assert _has_seed_block(lines) is True


def test_has_seed_block_false_when_marker_after_fence() -> None:
    # The marker must come before the fence; a fence before the marker does not
    # count as a THE SEED block.
    lines = [FENCE, "some code", FENCE, "## THE SEED"]
    assert _has_seed_block(lines) is False


def test_has_seed_block_false_when_no_marker() -> None:
    lines = ["# title", "", FENCE, "code", FENCE]
    assert _has_seed_block(lines) is False


def test_has_seed_block_false_when_marker_with_no_fence() -> None:
    lines = ["# title", "## THE SEED", "no fence here"]
    assert _has_seed_block(lines) is False
