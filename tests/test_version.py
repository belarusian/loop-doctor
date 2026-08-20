"""Tests for the single-source-of-truth version (Cycle 12).

The version in ``pyproject.toml`` and ``loop_doctor.__version__`` must agree,
and the CLI ``--version`` flag must surface that same value. The pyproject
version is parsed with a plain regex (no ``tomllib``) so the test has no
dependency on the stdlib TOML parser.
"""

from __future__ import annotations

import re
from pathlib import Path

from loop_doctor import __version__
from loop_doctor.cli import main

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _pyproject_version() -> str:
    """Extract the ``[project]`` version string from pyproject.toml via regex."""
    text = _PYPROJECT.read_text(encoding="utf-8")
    match = re.search(r'^version\s*=\s*"([^"]+)"', text, flags=re.MULTILINE)
    assert match is not None, "no [project] version found in pyproject.toml"
    return match.group(1)


def test_pyproject_version_matches_module_version() -> None:
    assert _pyproject_version() == __version__


def test_version_is_semver() -> None:
    assert re.fullmatch(r"\d+\.\d+\.\d+", __version__) is not None


def test_cli_version_flag_returns_zero_and_prints_version(capsys) -> None:
    code = main(["--version"])
    assert code == 0
    out = capsys.readouterr().out
    assert f"loop-doctor {__version__}" in out
