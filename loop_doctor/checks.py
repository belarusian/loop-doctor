"""Check registry for loop-doctor.

A check is a named callable ``fn(project_dir: Path) -> Check``. Checks are
registered by name in a module-level registry and composed into a single
``Report`` by the CLI. ``run_all`` runs every registered check in a stable
registration order and returns the list of ``Check`` results.

This module is dependency-free: it imports only from ``loop_doctor.project``,
``loop_doctor.protocol``, and ``loop_doctor.report`` (no spoke-lint / fourseer).
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from loop_doctor.project import resolve_project
from loop_doctor.prompt import prompt_check
from loop_doctor.protocol import protocol_check
from loop_doctor.report import Check, Status

# A check is a callable that takes a project dir and returns a Check.
CheckFn = Callable[[Path], Check]

# Module-level registry: check name -> check callable. Insertion order is the
# stable order used by run_all.
_REGISTRY: dict[str, CheckFn] = {}


def register(name: str, fn: CheckFn) -> None:
    """Register a named check.

    ``fn`` must be a callable ``fn(project_dir: Path) -> Check``. Registering a
    name that already exists replaces the previous callable but preserves the
    original registration position, so ``run_all`` order stays stable.
    """
    _REGISTRY[name] = fn


def registered_names() -> list[str]:
    """Return the registered check names in stable registration order."""
    return list(_REGISTRY.keys())


def run_all(project_dir: Path) -> list[Check]:
    """Run every registered check in stable registration order.

    Returns the list of ``Check`` results, one per registered check, in the
    order the checks were registered.
    """
    project_dir = Path(project_dir)
    return [fn(project_dir) for fn in _REGISTRY.values()]


def run_one(name: str, project_dir: Path) -> Check:
    """Run a single named check and return its ``Check`` result.

    Raises ``KeyError`` if ``name`` is not a registered check.
    """
    if name not in _REGISTRY:
        raise KeyError(name)
    return _REGISTRY[name](Path(project_dir))


def _foundation(project_dir: Path) -> Check:
    """The foundation check: the ``ai`` dir resolves and the 3-file set is located.

    Passes when both the gate log and the runner prompt are located; otherwise
    fails with a detail naming what is missing. Reuses
    :func:`loop_doctor.project.resolve_project`.
    """
    ai_dir, three = resolve_project(project_dir)
    if three.gate_log is not None and three.runner_prompt is not None:
        return Check("foundation", Status.PASS, f"ai dir {ai_dir}")
    missing = []
    if three.gate_log is None:
        missing.append("gate log")
    if three.runner_prompt is None:
        missing.append("runner prompt")
    return Check("foundation", Status.FAIL, "missing: " + ", ".join(missing))


# Register the foundation check at import time so run_all returns it with no
# extra setup.
register("foundation", _foundation)

# Register the protocol check after foundation so run_all returns
# [foundation, protocol] in stable order.
register("protocol", protocol_check)

# Register the prompt check after protocol so run_all returns
# [foundation, protocol, prompt] in stable order.
register("prompt", prompt_check)
