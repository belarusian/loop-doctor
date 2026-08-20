"""Tests for loop_doctor.prompt: the prompt lint check PASS/FAIL/SKIP cases.

All tests are deterministic and network-free. A fake spokes dir with a minimal
argparse spoke script is built under ``tmp_path`` and the runner prompt
references it. The ``spoke_lint`` import is patched to simulate absence for the
SKIP case. The real-dep PASS/FAIL tests are guarded with
``pytest.importorskip("spoke_lint")`` so the suite is green with or without the
``full`` extra.
"""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace
from unittest import mock

import pytest

from loop_doctor.prompt import (
    _DEFAULT_SPOKES_DIR,
    _format_findings,
    _invocation_findings,
    _resolve_spokes_dir,
    prompt_check,
)
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
    pytest.importorskip("spoke_lint")
    spokes_dir = tmp_path / "spokes"
    prompt = f"python {spokes_dir}/foo.py --goal x --max-steps 5"
    _make_project(tmp_path, prompt_text=prompt, spokes={"foo.py": _SPOKE})
    check = prompt_check(tmp_path)
    assert check.name == "prompt"
    assert check.status is Status.PASS


def test_prompt_pass_detail_is_exact(tmp_path: Path) -> None:
    pytest.importorskip("spoke_lint")
    # The PASS detail is pinned exactly: "ai dir <resolved ai dir>".
    spokes_dir = tmp_path / "spokes"
    prompt = f"python {spokes_dir}/foo.py --goal x"
    _make_project(tmp_path, prompt_text=prompt, spokes={"foo.py": _SPOKE})
    check = prompt_check(tmp_path)
    assert check.detail == f"ai dir {tmp_path / 'ai'}"


def test_prompt_fails_on_unknown_flag(tmp_path: Path) -> None:
    pytest.importorskip("spoke_lint")
    spokes_dir = tmp_path / "spokes"
    prompt = f"python {spokes_dir}/foo.py --goal x --bogus y"
    _make_project(tmp_path, prompt_text=prompt, spokes={"foo.py": _SPOKE})
    check = prompt_check(tmp_path)
    assert check.status is Status.FAIL
    assert "unknown_flag" in check.detail
    assert "bogus" in check.detail


def test_prompt_fails_on_missing_script(tmp_path: Path) -> None:
    pytest.importorskip("spoke_lint")
    spokes_dir = tmp_path / "spokes"
    prompt = f"python {spokes_dir}/nope.py --goal x"
    _make_project(tmp_path, prompt_text=prompt, spokes={"foo.py": _SPOKE})
    check = prompt_check(tmp_path)
    assert check.status is Status.FAIL
    assert "missing_script" in check.detail


def test_prompt_fails_on_missing_required_flag(tmp_path: Path) -> None:
    pytest.importorskip("spoke_lint")
    # The required --goal flag is absent -> a missing_required finding.
    spokes_dir = tmp_path / "spokes"
    prompt = f"python {spokes_dir}/foo.py --max-steps 5"
    _make_project(tmp_path, prompt_text=prompt, spokes={"foo.py": _SPOKE})
    check = prompt_check(tmp_path)
    assert check.status is Status.FAIL
    assert "missing_required" in check.detail
    assert "goal" in check.detail


def test_prompt_fails_with_multiple_findings_detail_format(tmp_path: Path) -> None:
    pytest.importorskip("spoke_lint")
    # Two invocations in one prompt: one unknown flag, one missing required.
    # The detail is the "; "-joined "kind: flag" strings in invocation order.
    spokes_dir = tmp_path / "spokes"
    prompt = NL.join([
        f"python {spokes_dir}/foo.py --goal x --bogus y",
        f"python {spokes_dir}/foo.py --max-steps 5",
    ])
    _make_project(tmp_path, prompt_text=prompt, spokes={"foo.py": _SPOKE})
    check = prompt_check(tmp_path)
    assert check.status is Status.FAIL
    assert check.detail == "unknown_flag: bogus; missing_required: goal"


def test_prompt_multiple_invocations_one_invalid(tmp_path: Path) -> None:
    pytest.importorskip("spoke_lint")
    # Two invocations: the first is valid, the second has an unknown flag. Only
    # the invalid one produces a finding.
    spokes_dir = tmp_path / "spokes"
    prompt = NL.join([
        f"python {spokes_dir}/foo.py --goal x",
        f"python {spokes_dir}/foo.py --goal x --bogus y",
    ])
    _make_project(tmp_path, prompt_text=prompt, spokes={"foo.py": _SPOKE})
    check = prompt_check(tmp_path)
    assert check.status is Status.FAIL
    assert check.detail == "unknown_flag: bogus"


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


def test_resolve_spokes_dir_default_when_no_reference() -> None:
    # No "/spokes" reference in the text -> the default spokes dir.
    assert _resolve_spokes_dir("python foo.py --goal x") == _DEFAULT_SPOKES_DIR
    assert _resolve_spokes_dir("no path here at all") == Path("spokes")


def test_resolve_spokes_dir_from_reference() -> None:
    # A "/spokes" reference is extracted verbatim.
    text = "python /home/sasha/Research/four/examples/spokes/foo.py --goal x"
    assert _resolve_spokes_dir(text) == Path("/home/sasha/Research/four/examples/spokes")


def test_resolve_spokes_dir_expands_tilde() -> None:
    # A "~"-prefixed reference is expanded to the user home.
    text = "python ~/Research/four/examples/spokes/foo.py --goal x"
    assert _resolve_spokes_dir(text) == Path("~/Research/four/examples/spokes").expanduser()


def test_invocation_findings_drops_gate_command_findings() -> None:
    # Only invocation kinds are kept; missing_tool (gate-command) is dropped.
    findings = [
        SimpleNamespace(kind="missing_tool", flag="pytest"),
        SimpleNamespace(kind="unknown_flag", flag="bogus"),
        SimpleNamespace(kind="missing_script", flag="nope.py"),
        SimpleNamespace(kind="missing_required", flag="goal"),
    ]
    kept = _invocation_findings(findings)
    assert [f.kind for f in kept] == ["unknown_flag", "missing_script", "missing_required"]


def test_invocation_findings_empty_when_only_gate_command() -> None:
    findings = [SimpleNamespace(kind="missing_tool", flag="pytest")]
    assert _invocation_findings(findings) == []


def test_format_findings_joins_kind_and_flag() -> None:
    findings = [
        SimpleNamespace(kind="unknown_flag", flag="bogus"),
        SimpleNamespace(kind="missing_required", flag="goal"),
    ]
    assert _format_findings(findings) == "unknown_flag: bogus; missing_required: goal"


def test_format_findings_empty() -> None:
    assert _format_findings([]) == ""
