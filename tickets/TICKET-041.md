# TICKET-041 — Add a top-level summary field to render_json

## Title
`loop_doctor/report.py::render_json` must emit a top-level `summary` field
holding the same stable status-count string that `Report.summary()` returns
(e.g. `pass=3 fail=1 warn=1 skip=1`). Keep `sort_keys=True` and `indent=2` so
the output stays byte-stable. This closes the gap where the JSON output omits
the summary that the text path and `Report.summary()` already expose.

## Evidence
- `loop_doctor/report.py::render_json` currently emits only `verdict` and
  `checks`; the `summary` string is available via `Report.summary()` but is not
  in the JSON payload.
- `loop_doctor/report.py::Report.summary()` returns the fixed-order count line.
- Cycle 9 briefing "What to Build" row `loop_doctor/report.py`: "Add a
  top-level summary field to render_json (the same stable status-count string
  that Report.summary() returns) ... Keep sort_keys=True and indent=2."

## Impact
- Machine consumers of the JSON cannot read the aggregate status counts without
  re-deriving them from `checks`.

## Suggestion
- Add `"summary": report.summary()` to the payload dict. The change is additive
  and byte-stable; the ONE exact-string JSON test in `tests/test_report.py`
  must be updated to include the new field.
