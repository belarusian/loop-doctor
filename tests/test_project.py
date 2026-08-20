"""Tests for loop_doctor.project: ai-dir resolution and 3-file location."""

from __future__ import annotations

from pathlib import Path

from loop_doctor.checks import run_one
from loop_doctor.project import (
    ThreeFiles,
    _first_match,
    _parse_seed_ref,
    locate_three_files,
    resolve_ai_dir,
    resolve_proj_dir,
    resolve_project,
)
from loop_doctor.report import Status

FENCE = chr(96) * 3
TILDE_FENCE = "~~~"
NL = chr(10)

GATE_LOG = NL.join([
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


def _make_ai_dir(ai_dir, *, gate=True, seed_block=True):
    ai_dir.mkdir(parents=True, exist_ok=True)
    if gate:
        if seed_block:
            content = GATE_LOG
        else:
            content = NL.join(["# cycle-001 gate", "", "no seed block here", ""])
        (ai_dir / "cycle-001-loop-doctor-gate.md").write_text(content, encoding="utf-8")
    (ai_dir / "loop-doctor-cycle-runner-prompt.md").write_text(
        NL.join(["# runner prompt", ""]), encoding="utf-8")


def test_resolve_ai_dir_from_proj(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    assert resolve_ai_dir(proj) == tmp_path / "ai"


def test_resolve_ai_dir_from_parent(tmp_path):
    assert resolve_ai_dir(tmp_path) == tmp_path / "ai"


def test_resolve_ai_dir_from_ai_named_dir(tmp_path):
    # A dir not named "proj" is treated as the parent, so a dir literally named
    # "ai" yields ai/ai (the parent-treatment branch).
    ai = tmp_path / "ai"
    ai.mkdir()
    assert resolve_ai_dir(ai) == ai / "ai"


def test_resolve_proj_dir_from_proj(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    assert resolve_proj_dir(proj) == proj


def test_resolve_proj_dir_from_parent(tmp_path):
    assert resolve_proj_dir(tmp_path) == tmp_path / "proj"


def test_locate_three_files_all_present(tmp_path):
    ai_dir = tmp_path / "ai"
    _make_ai_dir(ai_dir)
    three = locate_three_files(ai_dir)
    assert three.gate_log == ai_dir / "cycle-001-loop-doctor-gate.md"
    assert three.runner_prompt == ai_dir / "loop-doctor-cycle-runner-prompt.md"
    assert three.seed_ref == Path("/home/sasha/Research/four")


def test_locate_three_files_gate_log_missing(tmp_path):
    ai_dir = tmp_path / "ai"
    _make_ai_dir(ai_dir, gate=False)
    three = locate_three_files(ai_dir)
    assert three.gate_log is None
    assert three.seed_ref is None
    assert three.runner_prompt == ai_dir / "loop-doctor-cycle-runner-prompt.md"


def test_locate_three_files_seed_block_missing(tmp_path):
    ai_dir = tmp_path / "ai"
    _make_ai_dir(ai_dir, seed_block=False)
    three = locate_three_files(ai_dir)
    assert three.gate_log is not None
    assert three.seed_ref is None


def test_locate_three_files_missing_ai_dir(tmp_path):
    three = locate_three_files(tmp_path / "does-not-exist")
    assert three == ThreeFiles(gate_log=None, runner_prompt=None, seed_ref=None)


def test_locate_three_files_when_ai_dir_is_a_file(tmp_path):
    # A regular file where the ai dir is expected: _first_match's is_dir()
    # guard returns None for every field.
    fake = tmp_path / "ai"
    fake.write_text("not a dir", encoding="utf-8")
    three = locate_three_files(fake)
    assert three == ThreeFiles(gate_log=None, runner_prompt=None, seed_ref=None)


def test_resolve_project_returns_ai_dir_and_files(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    _make_ai_dir(tmp_path / "ai")
    ai_dir, three = resolve_project(proj)
    assert ai_dir == tmp_path / "ai"
    assert three.seed_ref == Path("/home/sasha/Research/four")


def test_first_match_returns_first_sorted(tmp_path):
    ai = tmp_path / "ai"
    ai.mkdir()
    (ai / "cycle-002-b-gate.md").write_text("x")
    (ai / "cycle-001-a-gate.md").write_text("x")
    (ai / "cycle-003-c-gate.md").write_text("x")
    assert _first_match(ai, "cycle-*-*-gate.md") == ai / "cycle-001-a-gate.md"


def test_first_match_ignores_directories(tmp_path):
    ai = tmp_path / "ai"
    ai.mkdir()
    (ai / "cycle-001-a-gate.md").mkdir()  # a directory matching the pattern
    (ai / "cycle-002-b-gate.md").write_text("x")  # a real file
    assert _first_match(ai, "cycle-*-*-gate.md") == ai / "cycle-002-b-gate.md"


def test_first_match_no_match_returns_none(tmp_path):
    ai = tmp_path / "ai"
    ai.mkdir()
    (ai / "unrelated.txt").write_text("x")
    assert _first_match(ai, "cycle-*-*-gate.md") is None


def test_first_match_missing_dir_returns_none(tmp_path):
    assert _first_match(tmp_path / "nope", "cycle-*-*-gate.md") is None


def test_parse_seed_ref_no_marker_returns_none(tmp_path):
    gate = tmp_path / "gate.md"
    gate.write_text(NL.join(["# title", "no seed here", ""]), encoding="utf-8")
    assert _parse_seed_ref(gate) is None


def test_parse_seed_ref_marker_with_no_fence_returns_none(tmp_path):
    gate = tmp_path / "gate.md"
    gate.write_text(NL.join(["# title", "## THE SEED", "but no fence follows"]), encoding="utf-8")
    assert _parse_seed_ref(gate) is None


def test_parse_seed_ref_empty_fence_returns_none(tmp_path):
    gate = tmp_path / "gate.md"
    gate.write_text(NL.join(["# title", "## THE SEED", FENCE, FENCE, ""]), encoding="utf-8")
    assert _parse_seed_ref(gate) is None


def test_parse_seed_ref_skips_leading_blank_lines(tmp_path):
    # Blank lines inside the fence before the path are skipped.
    gate = tmp_path / "gate.md"
    gate.write_text(
        NL.join(["# title", "## THE SEED", FENCE, "", "", "/home/sasha/Research/four", FENCE]),
        encoding="utf-8",
    )
    assert _parse_seed_ref(gate) == Path("/home/sasha/Research/four")


def test_parse_seed_ref_accepts_tilde_fence(tmp_path):
    gate = tmp_path / "gate.md"
    gate.write_text(
        NL.join(["# title", "## THE SEED", TILDE_FENCE, "/home/sasha/Research/four", TILDE_FENCE]),
        encoding="utf-8",
    )
    assert _parse_seed_ref(gate) == Path("/home/sasha/Research/four")


def test_parse_seed_ref_unreadable_returns_none(tmp_path):
    # A gate log that cannot be read as UTF-8 -> None (no exception).
    gate = tmp_path / "gate.md"
    gate.write_bytes(b"\xff\xfe\x00THE SEED" + b"\x00" * 8)
    assert _parse_seed_ref(gate) is None


def test_foundation_check_pass_detail(tmp_path):
    # The foundation check PASSes with the exact "ai dir <path>" detail.
    proj = tmp_path / "proj"
    proj.mkdir()
    _make_ai_dir(tmp_path / "ai")
    check = run_one("foundation", proj)
    assert check.name == "foundation"
    assert check.status is Status.PASS
    assert check.detail == f"ai dir {tmp_path / 'ai'}"


def test_foundation_check_fails_naming_missing(tmp_path):
    # A project with a gate log but no runner prompt -> FAIL naming it.
    ai = tmp_path / "ai"
    ai.mkdir()
    (ai / "cycle-001-loop-doctor-gate.md").write_text(GATE_LOG, encoding="utf-8")
    check = run_one("foundation", tmp_path)
    assert check.status is Status.FAIL
    assert check.detail == "missing: runner prompt"


def test_foundation_check_fails_when_both_missing(tmp_path):
    # No gate log and no runner prompt -> FAIL naming both, in order.
    ai = tmp_path / "ai"
    ai.mkdir()
    check = run_one("foundation", tmp_path)
    assert check.status is Status.FAIL
    assert check.detail == "missing: gate log, runner prompt"
