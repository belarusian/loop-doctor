"""Tests for loop_doctor.bash_check: the bash syntax check PASS/FAIL cases.

All tests are deterministic and network-free. Driver scripts are written under
a ``proj`` dir in ``tmp_path`` and ``bash -n`` is run on each. The proj dir is
resolved via :func:`loop_doctor.project.resolve_proj_dir`, so the project root
is ``tmp_path`` and the drivers live in ``tmp_path / "proj"``.
"""

from __future__ import annotations

from pathlib import Path

from loop_doctor.bash_check import bash_check
from loop_doctor.report import Status

NL = chr(10)

# A driver that parses cleanly.
_GOOD = NL.join([
    "#!/usr/bin/env bash",
    "set -euo pipefail",
    "echo hello",
    "",
])

# A driver with a syntax error: an unterminated if block.
_BAD = NL.join([
    "#!/usr/bin/env bash",
    "if [ -z $x; then",
    "  echo hi",
    "",
])


def _make_proj(tmp_path: Path, drivers: dict[str, str]) -> Path:
    """Create ``tmp_path / "proj"`` with the given ``name -> content`` drivers."""
    proj = tmp_path / "proj"
    proj.mkdir(parents=True, exist_ok=True)
    for name, content in drivers.items():
        (proj / name).write_text(content, encoding="utf-8")
    return tmp_path


def test_bash_pass_when_no_drivers(tmp_path: Path) -> None:
    # A proj dir with no .sh files.
    (tmp_path / "proj").mkdir()
    check = bash_check(tmp_path)
    assert check.name == "bash"
    assert check.status is Status.PASS
    assert check.detail == "no .sh drivers"


def test_bash_pass_when_no_proj_dir(tmp_path: Path) -> None:
    # No proj dir at all -> no drivers -> PASS.
    check = bash_check(tmp_path)
    assert check.status is Status.PASS
    assert check.detail == "no .sh drivers"


def test_bash_pass_when_valid_driver(tmp_path: Path) -> None:
    _make_proj(tmp_path, {"run.sh": _GOOD})
    check = bash_check(tmp_path)
    assert check.name == "bash"
    assert check.status is Status.PASS
    assert "parse cleanly" in check.detail


def test_bash_pass_when_multiple_valid_drivers(tmp_path: Path) -> None:
    _make_proj(tmp_path, {"a.sh": _GOOD, "b.sh": _GOOD})
    check = bash_check(tmp_path)
    assert check.status is Status.PASS
    assert "parse cleanly" in check.detail


def test_bash_fails_on_syntax_error(tmp_path: Path) -> None:
    _make_proj(tmp_path, {"run.sh": _BAD})
    check = bash_check(tmp_path)
    assert check.name == "bash"
    assert check.status is Status.FAIL
    assert "run.sh" in check.detail
    assert "syntax error" in check.detail


def test_bash_names_offending_script_among_valid_ones(tmp_path: Path) -> None:
    _make_proj(tmp_path, {"good.sh": _GOOD, "bad.sh": _BAD})
    check = bash_check(tmp_path)
    assert check.status is Status.FAIL
    # The offending script is named; the clean one is not.
    assert "bad.sh" in check.detail
    assert "good.sh" not in check.detail


def test_bash_ignores_non_sh_files(tmp_path: Path) -> None:
    # A .txt file in the proj dir is not a driver.
    _make_proj(tmp_path, {"notes.txt": "not a script"})
    check = bash_check(tmp_path)
    assert check.status is Status.PASS
    assert check.detail == "no .sh drivers"


def test_bash_ignores_subdirectory_sh_files(tmp_path: Path) -> None:
    # Only *.sh directly in the proj dir count; nested ones are ignored.
    proj = tmp_path / "proj"
    proj.mkdir()
    (proj / "run.sh").write_text(_GOOD, encoding="utf-8")
    nested = proj / "sub"
    nested.mkdir()
    (nested / "nested.sh").write_text(_BAD, encoding="utf-8")
    check = bash_check(tmp_path)
    assert check.status is Status.PASS
