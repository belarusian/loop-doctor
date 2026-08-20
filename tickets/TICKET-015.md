# TICKET-015 — No prompt check: the runner prompt's spoke invocations are not validated

## Title
There is no PROMPT LINT check. The Cycle 4 target `loop_doctor/prompt.py` does not
exist. Nothing validates that the runner prompt's spoke invocations (the
`python .../spokes/<name>.py --flag value` lines) match the argparse signatures of
the referenced spoke scripts. The `foundation` and `protocol` checks only confirm the
runner prompt is *located* and that the gate log is well-formed; they never parse the
prompt for spoke invocations.

## Evidence
- `ls loop_doctor/` — contains `__init__.py`, `checks.py`, `cli.py`, `project.py`,
  `protocol.py`, `report.py`. No `prompt.py`.
- `loop_doctor/checks.py` registers `foundation` and `protocol`. `run_all` returns
  `[foundation, protocol]`.
- `loop_doctor/project.py` already provides `resolve_project(project_dir) ->
  (ai_dir, ThreeFiles)` where `ThreeFiles.runner_prompt` is the located runner prompt
  path (`Path | None`).
- The `spoke_lint` library (installed, importable) exposes
  `spoke_lint.diff_prompt(text, spokes_dir, path=None) -> list[Finding]`; each
  `Finding` has `kind`, `flag`, `message`.
- Cycle 4 briefing "What to Build" row `loop_doctor/prompt.py` (NEW): "a
  `prompt_check(project_dir) -> Check` named `prompt`. Reuse `project.resolve_project`
  to get the runner prompt. Read the prompt text and run `spoke_lint.diff_prompt(text,
  spokes_dir)`. PASS when there are no findings; FAIL with a detail naming the
  findings."

## Impact
- The second of the five real capabilities (Cycles 3-8) is absent. A runner prompt that
  passes a flag a spoke does not accept, or references a spoke script that does not
  exist, would still be reported GO, masking a prompt that would fail at runtime.

## Suggestion
Create `loop_doctor/prompt.py` with:
- `prompt_check(project_dir: Path) -> Check` that reuses
  `loop_doctor.project.resolve_project` (do NOT re-implement resolution).
- Read the runner prompt text and run `spoke_lint.diff_prompt(text, spokes_dir)`.
- PASS when there are no invocation findings; FAIL with a detail naming the findings
  (e.g. "unknown_flag: --goal", "missing_script: ...").
- Keep the check dependency-free except for the optional `spoke_lint` import (see
  TICKET-017).
