# TICKET-010 — No protocol check: the 3-file set and gate-log well-formedness are not validated

## Title
There is no PROTOCOL CHECK. The Cycle 3 target `loop_doctor/protocol.py` does not
exist. Nothing verifies that the 3-file set (gate log + runner prompt + seed ref) is
fully present, nor that the gate log is well-formed (has a `# ...` title line and a
`## THE SEED` fenced block). The `foundation` check only confirms the gate log and
runner prompt are *located*; it does not parse the gate log for structure, and it does
not require the seed ref to be resolvable.

## Evidence
- `ls loop_doctor/` — contains `__init__.py`, `checks.py`, `cli.py`,
  `project.py`, `report.py`. No `protocol.py`.
- `loop_doctor/checks.py` registers only `foundation` (via
  `register("foundation", _foundation)`). `run_all` returns a single check.
- `loop_doctor/project.py` already provides the building blocks:
  `resolve_project(project_dir) -> (ai_dir, ThreeFiles)` and
  `locate_three_files(ai_dir) -> ThreeFiles` where `ThreeFiles` carries
  `gate_log`, `runner_prompt`, and `seed_ref` (each `Path | None`).
  `_parse_seed_ref` returns `None` when the `THE SEED` block is absent.
- Cycle 3 briefing "What to Build" row `loop_doctor/protocol.py` (NEW): "a
  `protocol_check(project_dir) -> Check` named `protocol`. PASS when the 3-file
  set is fully present (gate log + runner prompt + seed ref all located) AND the gate
  log is well-formed (has a `# ...` title line and a `## THE SEED` fenced
  block). FAIL with a detail naming exactly what is missing/malformed. Reuse
  `project.resolve_project` / `locate_three_files`; do not re-implement
  resolution. Keep it dependency-free."

## Impact
- The first of the five real capabilities (Cycles 3-8) is absent. The registry built in
  Cycle 2 has no protocol check to plug in, so `run_all` still returns only
  `foundation` and the aggregate verdict never reflects gate-log structure.
- A project with a gate log that is present but malformed (no title, no seed block)
  would still pass `foundation` and be reported GO, masking a broken protocol.

## Suggestion
Create `loop_doctor/protocol.py` with:
- `protocol_check(project_dir: Path) -> Check` that reuses
  `loop_doctor.project.resolve_project` (do NOT re-implement resolution).
- PASS when `three.gate_log`, `three.runner_prompt`, and `three.seed_ref`
  are all non-None AND the gate log text has a `# ...` title line (a line whose
  stripped form starts with `#` and has non-empty text after it) AND contains a
  `## THE SEED` fenced block (a line containing `THE SEED` followed by a
  fenced code block).
- FAIL with a detail that names exactly what is missing/malformed, e.g. "missing:
  seed ref" or "malformed gate log: no title line" or "malformed gate log: no THE SEED
  block". Keep it dependency-free (no spoke-lint / fourseer).
Add deterministic, network-free tests: PASS on a well-formed 3-file set; FAIL (with the
right detail) when the gate log is missing, the runner prompt is missing, the seed block
is absent, or the gate log lacks a title line.
