# TICKET-042 — Update the exact-string JSON test and add a JSON-summary-equals-Report.summary test

## Title
`tests/test_report.py` must (a) update the existing exact-string JSON test
`test_render_json_byte_stable_for_sample_report` to include the new `summary`
field in the expected payload, and (b) add a test that the JSON `summary` field
equals `Report.summary()` for a mixed-status report.

## Evidence
- `tests/test_report.py::test_render_json_byte_stable_for_sample_report` asserts
  the full JSON string; it will break once `render_json` adds `summary`.
- The sample report is `pass=1 fail=0 warn=1 skip=1`.
- Cycle 9 briefing "What to Build" row `tests/test_report.py`.

## Impact
- The byte-stable contract for the JSON output would be unpinned after the
  schema change.

## Suggestion
- Insert `'  "summary": "pass=1 fail=0 warn=1 skip=1",\n'` into the expected
  string (between `checks` and `verdict`, per `sort_keys`).
- Add a test asserting `json.loads(render_json(r))["summary"] == r.summary()`
  for a mixed-status report and for an empty report.
