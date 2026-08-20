# TICKET-006 — No check registry: named checks cannot compose into one Report

## Title
The Cycle 2 Foundation target `loop_doctor/checks.py` does not exist. There is no
check registry, so named checks cannot be registered and composed into a single
`Report` with one aggregate go/no-go verdict. The CLI currently hardcodes exactly
one `foundation` check inline.

## Evidence
- `ls loop_doctor/` — contains only `__init__.py`, `cli.py`, `project.py`,
  `report.py`. No `checks.py`.
- `loop_doctor/cli.py:28` `run_check(project_dir)` builds a single `Check` named
  "foundation" by hand and returns `Report(checks=[check])`. The check logic is
  inlined in the CLI, not in a reusable registry.
- `loop_doctor/cli.py:14` imports only `resolve_project`; nothing composes multiple
  checks.
- Cycle 2 briefing "What to Build" row `loop_doctor/checks.py`: "A check registry:
  register(name, fn) / run_all(project_dir) -> list[Check] so named checks compose
  into one Report. Ship one real check (foundation) that reuses
  project.resolve_project. Keep it dependency-free."
- Cycles 3-8 each add a real check (protocol, prompt-lint, bash, run-health,
  endpoint). Without a registry, each new check would need a new inline branch in
  `cli.py` and the aggregate verdict would have no single composition point.

## Impact
- The report model already supports a list of checks and an aggregate verdict
  (`report.py:40` `Report`, `report.py:51` `verdict`), but nothing populates it
  with more than one check. The "multiple named checks, single aggregate verdict"
  capability the Foundation is meant to deliver is absent.
- Cycles 3-8 have no extension point: adding a check means editing `cli.py` and
  re-deriving the verdict aggregation each time.
- The `foundation` check logic is duplicated in the CLI rather than living in one
  place that both the CLI and tests can call.

## Suggestion
Create `loop_doctor/checks.py` with:
- A module-level registry mapping check name to a callable
  `fn(project_dir: Path) -> Check`.
- `register(name: str, fn) -> None` — add a named check to the registry.
- `run_all(project_dir: Path) -> list[Check]` — run every registered check in a
  stable order (registration order) and return the list of `Check` results.
- Ship one real check named "foundation" that reuses
  `loop_doctor.project.resolve_project` (pass when the gate log and runner prompt
  are located; fail with a detail otherwise). Keep it dependency-free (no
  spoke-lint / fourseer imports).
- Register "foundation" at import time so `run_all` returns it with no extra setup.
Add deterministic, network-free tests: `run_all` returns a list containing a
"foundation" `Check`; registering a second check makes `run_all` return both, and
the composed `Report` carries a single aggregate verdict.
