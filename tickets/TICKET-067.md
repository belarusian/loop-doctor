# TICKET-067: ci check must resolve the git repo via `<project-dir>/proj`

## Capability
The ci check (check 7) must run its `git`/`gh` commands against the project's
**git repo**, which in the four-pipeline layout lives at `<project-dir>/proj`
— exactly as the bash check already does. Today it runs `git` in the raw
project dir, so a fleet-style layout (a `proj/` git repo with an `origin`
remote, sitting next to an `ai/` dir) is wrongly SKIPped as "no origin" and
the check never verifies CI at all.

## Evidence
- `loop_doctor/ci.py:104-110` — `ci_check` runs
  `git -C <project_dir> rev-parse --is-inside-work-tree` and
  `git -C <project_dir> remote get-url origin` directly on `project_dir`.
  It never calls `loop_doctor.project.resolve_proj_dir`.
- Contrast `loop_doctor/bash_check.py:40` — `bash_check` resolves the repo
  with `proj_dir = resolve_proj_dir(project_dir)` before touching the tree.
  The ci check is the only check that does not resolve `proj/`.
- Verified on this machine (fleet layout):
  - `git -C /home/sasha/AI/loop-doctor rev-parse --is-inside-work-tree` → `true`
    (the parent dir is inside the ambient `/home/sasha` git tree).
  - `git -C /home/sasha/AI/loop-doctor remote get-url origin` →
    `error: No such remote 'origin'`.
  - `git -C /home/sasha/AI/loop-doctor/proj remote get-url origin` →
    `https://github.com/belarusian/loop-doctor.git`.
  So `ci_check("/home/sasha/AI/loop-doctor")` returns
  `Check("ci", Status.SKIP, "not a git repo with origin")` even though the
  project's real repo (in `proj/`) has a GitHub `origin`.

## Impact
The ci check exists precisely because cycles 4-7 were red-on-CI while local
was green (see `docs/architecture.md` capability 6 and the Cycle 14 log). On
the canonical fleet layout it silently SKIPs, so a project with red CI still
passes the go/no-go — the exact failure the check was built to catch is
uncaught. The check is effectively dead on every real project.

## Suggestion
- In `ci_check`, resolve the repo first:
  `repo_dir = resolve_proj_dir(project_dir)` (import from
  `loop_doctor.project`, mirroring `bash_check`), and run every `git`/`gh`
  command with `-C str(repo_dir)` (or `gh` against `repo_dir`).
- Keep the SKIP-on-indeterminate convention: a `proj/` that is not a git
  work tree, has no `origin`, or is a non-GitHub remote still SKIPs.
- Update the `ci.py` module docstring (lines 1-16) and
  `docs/architecture.md` capability 6 to state the check resolves the `proj`
  git repo (not the raw project dir).
- Add a mocked test in `tests/test_ci.py` that drives the seam and asserts
  the `git -C` argument is the resolved `proj` path (not the raw project
  dir), and a test that a fleet layout (raw dir not a repo, `proj/` a repo
  with origin) reaches the green/red decision instead of SKIP.

## Acceptance
- `loop-doctor check ~/AI/loop-doctor/proj` and
  `loop-doctor check ~/AI/loop-doctor` both run the ci check against
  `~/AI/loop-doctor/proj` (the git repo) and do not SKIP as "no origin".
- The mocked suite pins the resolved `proj` path in the `git -C` argument.
- Gate green: `pytest tests/ -x -q`, `ruff check loop_doctor/`,
  `mypy loop_doctor/ --ignore-missing-imports`.
