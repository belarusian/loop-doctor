# TICKET-017 — Prompt check must degrade gracefully when spoke_lint is absent (SKIP) and FAIL when the prompt is missing

## Title
`spoke_lint` is an optional `full` extra, not a hard dependency. The prompt check must
not crash when `spoke_lint` is not importable; it must return `Status.SKIP` (non-blocking)
with a detail like "spoke-lint not installed". Separately, when the runner prompt itself
is missing (not located by `resolve_project`), the check must FAIL naming it.

## Evidence
- `pyproject.toml` lists `spoke-lint` under `[project.optional-dependencies] full`, not
  under `dependencies`.
- `loop_doctor/report.py` `Status` has `SKIP = "skip"` and the verdict treats SKIP as
  non-blocking (only FAIL blocks).
- `loop_doctor/project.py` `ThreeFiles.runner_prompt` is `Path | None`; it is `None`
  when the runner prompt is not located.
- Cycle 4 briefing: "if `spoke_lint` is not importable, return `Status.SKIP`
  (non-blocking) with a detail like 'spoke-lint not installed'; if the runner prompt is
  missing, FAIL naming it. Keep the check itself dependency-free except for the optional
  `spoke_lint` import (guard it with try/except ImportError)."

## Impact
- Without the guard, importing `loop_doctor.prompt` (and therefore `checks`) would raise
  `ImportError` in a minimal install, breaking the whole CLI.
- Without the missing-prompt branch, a project with no runner prompt would crash or
  misreport instead of FAILing with a clear detail.

## Suggestion
- Guard the import: `try: import spoke_lint except ImportError: spoke_lint = None` at
  module level (or inside the check). When `spoke_lint is None`, return
  `Check("prompt", Status.SKIP, "spoke-lint not installed")`.
- When `three.runner_prompt is None`, return
  `Check("prompt", Status.FAIL, "missing: runner prompt")`.
- Order of checks: missing prompt (FAIL) takes precedence over the spoke_lint guard so a
  project with no prompt is never silently SKIPped.
