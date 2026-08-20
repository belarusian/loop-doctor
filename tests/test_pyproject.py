"""Tests for the dependency boundary in pyproject.toml (TICKET-005)."""

from __future__ import annotations

from pathlib import Path

_PYPROJECT = Path(__file__).resolve().parent.parent / "pyproject.toml"


def _text() -> str:
    return _PYPROJECT.read_text(encoding="utf-8")


def test_base_dependencies_are_empty() -> None:
    assert "dependencies = []" in _text()


def test_git_deps_moved_to_full_extra() -> None:
    text = _text()
    assert "full = [" in text
    assert "spoke-lint @ git+" in text
    assert "fourseer @ git+" in text


def test_entry_point_preserved() -> None:
    assert "loop-doctor = " + chr(34) + "loop_doctor.cli:main" + chr(34) in _text()


def test_project_urls_table_present() -> None:
    text = _text()
    assert "[project.urls]" in text
    assert "github.com/belarusian/loop-doctor" in text
