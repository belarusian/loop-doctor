"""Tests for loop_doctor.project: ai-dir resolution and 3-file location."""

from __future__ import annotations

from pathlib import Path

from loop_doctor.project import (
    ThreeFiles,
    locate_three_files,
    resolve_ai_dir,
    resolve_project,
)

FENCE = chr(96) * 3
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


def test_resolve_project_returns_ai_dir_and_files(tmp_path):
    proj = tmp_path / "proj"
    proj.mkdir()
    _make_ai_dir(tmp_path / "ai")
    ai_dir, three = resolve_project(proj)
    assert ai_dir == tmp_path / "ai"
    assert three.seed_ref == Path("/home/sasha/Research/four")
