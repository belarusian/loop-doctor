"""GitHub Actions CI check for loop-doctor.

The ci check verifies that the project's main-branch head commit has green
GitHub Actions CI. It resolves the origin remote, fetches ``origin/main``, and
queries the GitHub API for the check runs on that commit via ``gh``.

The check is dependency-free except for the ``git`` and ``gh`` binaries, which
are invoked through a single module-level seam :func:`_run`. In tests the seam
is isolated by patching ``loop_doctor.ci._run`` (see ``tests/test_ci.py``), so
the suite stays deterministic and network-free.

An indeterminate environment (missing ``gh``, a non-git directory, a
non-GitHub remote, or a failed subprocess) is surfaced as ``Status.SKIP``
(non-blocking) rather than a hard FAIL, mirroring the prompt check's
optional-dependency SKIP convention.
"""

from __future__ import annotations

import json
import re
import subprocess
from pathlib import Path

from loop_doctor.report import Check, Status

# Conclusions that mean a check run did not block the commit.
_OK_CONCLUSIONS = frozenset({"success", "neutral", "skipped"})

# Conclusions that mean a check run blocked the commit.
_BAD_CONCLUSIONS = frozenset({"failure", "cancelled", "timed_out", "action_required"})

# https://github.com/{owner}/{name} with an optional trailing ".git".
_HTTPS_GITHUB_RE = re.compile(r"^https://github\.com/([^/]+)/([^/]+?)(?:\.git)?/?$")

# git@github.com:{owner}/{name}.git
_SSH_GITHUB_RE = re.compile(r"^git@github\.com:([^/]+)/([^/]+?)(?:\.git)?$")


def _run(cmd: list[str]) -> subprocess.CompletedProcess:
    """Run ``cmd`` and return the ``CompletedProcess``.

    This is the single subprocess seam for the ci check. A missing binary
    (``FileNotFoundError``) is normalized to a non-zero ``returncode`` result
    (``127``) with a ``command not found`` stderr, so a missing ``gh`` is a
    SKIP rather than an exception.
    """
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            check=False,
        )
    except FileNotFoundError:
        return subprocess.CompletedProcess(
            args=cmd,
            returncode=127,
            stdout="",
            stderr=f"{cmd[0]}: command not found",
        )


def _parse_github_remote(url: str) -> tuple[str, str] | None:
    """Return ``(owner, name)`` for a supported GitHub remote URL, else ``None``.

    Only the ``https://github.com/{owner}/{name}`` form (with an optional
    trailing ``.git``) and the ``git@github.com:{owner}/{name}.git`` form are
    supported.
    """
    url = url.strip()
    m = _HTTPS_GITHUB_RE.match(url)
    if m is not None:
        return m.group(1), m.group(2)
    m = _SSH_GITHUB_RE.match(url)
    if m is not None:
        return m.group(1), m.group(2)
    return None


def _short_sha(sha: str) -> str:
    """Return the short (7-char) form of a commit SHA."""
    return sha[:7]


def _tail(text: str, limit: int = 200) -> str:
    """Return the trailing ``limit`` characters of ``text`` (for detail strings)."""
    text = text.strip()
    if len(text) <= limit:
        return text
    return text[-limit:]


def ci_check(project_dir: Path) -> Check:
    """The ci check: the project's main-branch head commit has green CI.

    Resolves the origin remote, fetches ``origin/main``, and evaluates the
    GitHub Actions check runs on that commit. See the module docstring for the
    decision order. Any indeterminate environment is surfaced as ``SKIP``
    (non-blocking).
    """
    project_dir = Path(project_dir)

    # 1. Must be a git work tree with an origin remote.
    inside = _run(["git", "-C", str(project_dir), "rev-parse", "--is-inside-work-tree"])
    if inside.returncode != 0:
        return Check("ci", Status.SKIP, "not a git repo with origin")
    remote = _run(["git", "-C", str(project_dir), "remote", "get-url", "origin"])
    if remote.returncode != 0 or not remote.stdout.strip():
        return Check("ci", Status.SKIP, "not a git repo with origin")

    # 2. Parse owner/name from the origin URL.
    parsed = _parse_github_remote(remote.stdout)
    if parsed is None:
        return Check("ci", Status.SKIP, "non-GitHub remote")
    owner, name = parsed

    # 3. Fetch origin/main and resolve its head SHA.
    fetch = _run(["git", "-C", str(project_dir), "fetch", "origin", "main", "--quiet"])
    rev = _run(["git", "-C", str(project_dir), "rev-parse", "origin/main"])
    if rev.returncode != 0 or not rev.stdout.strip():
        return Check(
            "ci",
            Status.SKIP,
            "cannot resolve origin/main: " + _tail(rev.stderr or rev.stdout),
        )
    sha = rev.stdout.strip()
    short = _short_sha(sha)
    fetch_note = ""
    if fetch.returncode != 0:
        fetch_note = " (using local origin/main ref)"

    # 4. Query the GitHub API for the check runs on this commit.
    api = _run(
        ["gh", "api", f"repos/{owner}/{name}/commits/{sha}/check-runs"]
    )
    if api.returncode != 0:
        return Check("ci", Status.SKIP, "gh check-runs failed: " + _tail(api.stderr or api.stdout))
    try:
        payload = json.loads(api.stdout)
    except (json.JSONDecodeError, ValueError):
        return Check("ci", Status.SKIP, "invalid check-runs JSON: " + _tail(api.stdout))

    runs = payload.get("check_runs", []) if isinstance(payload, dict) else []
    if not runs:
        return Check("ci", Status.SKIP, f"no check runs for {short}")

    total = len(runs)
    completed = [r for r in runs if r.get("status") == "completed"]
    if len(completed) < total:
        return Check(
            "ci",
            Status.FAIL,
            f"CI in progress for {short}: {len(completed)}/{total} completed",
        )

    bad = [
        r.get("name", "unnamed")
        for r in runs
        if r.get("conclusion") in _BAD_CONCLUSIONS
    ]
    if bad:
        return Check("ci", Status.FAIL, f"CI red at {short}: " + ", ".join(bad))

    # All runs completed with an OK conclusion.
    return Check("ci", Status.PASS, f"CI green at {short}{fetch_note}")
