# TICKET-005 — Foundation is coupled to two external git deps it does not use yet

## Title
`pyproject.toml` lists `spoke-lint` and `fourseer` as hard install dependencies,
but the Foundation modules (CLI, dir resolution, report model) do not import them.
Installing the package therefore requires fetching two external git repos before
any Foundation code can be built or tested.

## Evidence
- `pyproject.toml:12-15` declares:
  - `spoke-lint @ git+https://github.com/belarusian/spoke-lint.git`
  - `fourseer @ git+https://github.com/belarusian/fourseer.git`
- `loop_doctor/` currently contains only `__init__.py`; the Foundation targets
  (`cli.py`, `project.py`, `report.py`) per the Cycle 1 briefing do not import
  `spoke_lint` or `fourseer`.
- Those libraries are only needed by later capabilities: PROMPT LINT (Cycle 3-4)
  uses spoke-lint; RUN HEALTH (Cycle 5-6) uses fourseer (ASSIGNMENT section 3).
- `.github/workflows/ci.yml` runs `pip install -e .` — so CI for the Foundation
  depends on two external git repos being reachable and installable.

## Impact
- `pip install -e .` (and thus `pytest`, `ruff`, `mypy`) fails if either git repo
  is unreachable, renamed, or requires auth — even though the Foundation code does
  not use them.
- Foundation development and its tests cannot run offline / in a hermetic CI.
- The "deterministic, fully tested before merge" gate is fragile: a flaky external
  fetch turns a Foundation PR red for reasons unrelated to its code.

## Suggestion
Decouple the Foundation from the external deps:
- Move `spoke-lint` and `fourseer` to an optional extra (e.g.
  `[project.optional-dependencies] full = [...]`) or add them only in the cycle
  that first imports them (PROMPT LINT / RUN HEALTH).
- Keep the base install dependency-free so `cli.py`, `project.py`, and
  `report.py` can be installed, tested, and gated hermetically.
- When a capability first imports a library, import it lazily inside the function
  (not at module top) so the CLI still runs and reports a SKIP/WARN for that check
  when the optional dep is absent, rather than crashing at import.
Document the dependency boundary in the README.
