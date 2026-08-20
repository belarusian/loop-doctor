# TICKET-003 — `loop_doctor/report.py` (report model + JSON/text renderers) is missing

## Title
There is no deterministic report model (checks, statuses, go/no-go verdict) and no
stable JSON/text renderers. The Foundation target `loop_doctor/report.py` from the
Cycle 1 briefing does not exist.

## Evidence
- `ls loop_doctor/` — only `__init__.py`; no `report.py`.
- Cycle 1 briefing "What to Build" lists `loop_doctor/report.py`: "Deterministic
  report model (checks, statuses, go/no-go verdict) + stable JSON and text
  renderers".
- `README.md` — "Output is fully deterministic." and documents `--json`.
- `pyproject.toml:17` — the CLI entrypoint (`loop_doctor.cli:main`) would need a
  report object to render, but none exists.
- The go/no-go semantics are defined by the ASSIGNMENT: the tool "returns a go or
  no-go report for launching build cycles", and the CLI contract is exit
  `0` go / `1` no-go / `2` usage error.

## Impact
- No shared data structure for a check result, so each future capability
  (protocol, prompt-lint, bash, run-health, endpoint) would invent its own shape —
  the report would not be deterministic or stable.
- The `--json` flag has nothing to serialize; the text renderer has nothing to
  format.
- The go/no-go verdict (and therefore the exit code) has no single place of
  definition, risking divergence between the CLI and the checks.

## Suggestion
Create `loop_doctor/report.py` with:
- `Status` enum (e.g. PASS / FAIL / WARN / SKIP) and a `Check` dataclass
  (`name: str`, `status: Status`, `detail: str`).
- A `Report` dataclass holding `checks: list[Check]` plus a derived
  `verdict: bool` (go) — define the aggregation rule explicitly (e.g. go only if
  no FAIL; document how WARN/SKIP affect the verdict).
- `render_text(report: Report) -> str` — stable, human-readable; deterministic
  ordering (sort or preserve insertion order, but never depend on dict/set
  iteration order).
- `render_json(report: Report) -> str` — stable JSON: `sort_keys=True`, fixed
  field order, no timestamps or hostnames (determinism requirement).
- A helper `exit_code(report: Report) -> int` mapping go→0, no-go→1, so the CLI
  and the checks share one source of truth.
Add unit tests asserting byte-stable output for a fixed report (run the renderer
twice, compare), JSON round-trips, and the verdict/exit-code mapping.
