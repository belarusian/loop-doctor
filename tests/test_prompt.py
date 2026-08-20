"""Tests for loop_doctor.prompt: the prompt lint check PASS/FAIL/SKIP cases.

All tests are deterministic and network-free. A fake spokes dir with a minimal
argparse spoke script is built under ``tmp_path`` and the runner prompt
references it. The ``spoke_lint`` import is patched to simulate absence for the
SKIP case.
"""

from __future__ import annotations

import sys
from pathlib import Path
from unittest import mock

from loop_doctor.prompt import prompt_check
from loop_doctor.report import Status

NL = chr(10)

# A minimal spoke script that accepts --goal (required) and --max-steps.
_SPOKE = NL.join([
    "import argparse",
    "parser = argparse.ArgumentParser()",
    'parser.add_argument("--goal", required=True)',
    'parser.add_argument("--max-steps", type=int, default=200)',
    "",
])


def _wellformed_gate() -> str:
    """A well-formed gate log: a level-1 title line and a THE SEED block."""
    return NL.join([
        "# cycle-001 gate",
        "",
        "## THE SEED",
        "",
        chr(96) * 3,
        "/home/sasha/Research/four",
        chr(96) * 3,
        "",
    ])


def _make_project(
    tmp_path: Path,
    *,
    prompt_text: str,
    spokes: dict[str, str] | None = None,
) -> Path:
    """Build a project under ``tmp_path`` with a custom runner prompt and spokes dir."""
    ai_dir = tmp_path / "ai"
    ai_dir.mkdir(parents=True, exist_ok=True)
    (ai_dir / "cycle-001-loop-doctor-gate.md").write_text(
        _wellformed_gate(), encoding="utf-8"
    )
    (ai_dir / "loop-doctor-cycle-runner-prompt.md").write_text(
        prompt_text, encoding="utf-8"
    )
    spokes_dir = tmp_path / "spokes"
    spokes_dir.mkdir(parents=True, exist_ok=True)
    for name, content in (spokes or {}).items():
        (spokes_dir / name).write_text(content, encoding="utf-8")
    return tmp_path


def test_prompt_pass_when_invocations_match_signatures(tmp_path: Path) -> None:
    spokes_dir = tmp_path / "spokes"
    prompt = f"python {spokes_dir}/foo.py --goal x --max-steps 5"
    _make_project(tmp_path, prompt_text=prompt, spokes={"foo.py": _SPOKE})
    check = prompt_check(tmp_path)
    assert check.name == "prompt"
    assert check.status is Status.PASS


def test_prompt_fails_on_unknown_flag(tmp_path: Path) -> None:
    spokes_dir = tmp_path / "spokes"
    prompt = f"python {spokes_dir}/foo.py --goal x --bogus y"
    _make_project(tmp_path, prompt_text=prompt, spokes={"foo.py": _SPOKE})
    check = prompt_check(tmp_path)
    assert check.status is Status.FAIL
    assert "unknown_flag" in check.detail
    assert "bogus" in check.detail


def test_prompt_fails_on_missing_script(tmp_path: Path) -> None:
    spokes_dir = tmp_path / "spokes"
    prompt = f"python {spokes_dir}/nope.py --goal x"
    _make_project(tmp_path, prompt_text=prompt, spokes={"foo.py": _SPOKE})
    check = prompt_check(tmp_path)
    assert check.status is Status.FAIL
    assert "missing_script" in check.detail


def test_prompt_skips_when_spoke_lint_not_importable(tmp_path: Path) -> None:
    spokes_dir = tmp_path / "spokes"
    prompt = f"python {spokes_dir}/foo.py --goal x"
    _make_project(tmp_path, prompt_text=prompt, spokes={"foo.py": _SPOKE})
    with mock.patch.dict(sys.modules, {"spoke_lint": None}):
        check = prompt_check(tmp_path)
    assert check.status is Status.SKIP
    assert "spoke-lint" in check.detail


def test_prompt_fails_when_runner_prompt_missing(tmp_path: Path) -> None:
    # A project with a gate log but no runner prompt.
    ai_dir = tmp_path / "ai"
    ai_dir.mkdir(parents=True, exist_ok=True)
    (ai_dir / "cycle-001-loop-doctor-gate.md").write_text(
        _wellformed_gate(), encoding="utf-8"
    )
    check = prompt_check(tmp_path)
    assert check.status is Status.FAIL
    assert "runner prompt" in check.detail
