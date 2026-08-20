# TICKET-054 — Add examples/ sample reports

## Title
Add an `examples/` directory with concrete sample loop-doctor reports (text and
JSON) so the documented output shape is illustrated with real, copy-pasteable
examples.

## Evidence
- No `examples/` directory exists.
- README.md documents the output shape abstractly but shows no concrete example.

## Impact
- A newcomer cannot verify they understand the output format without running the tool.

## Suggestion
- Create `examples/report.json` (a sample `--json` output: verdict true, a summary line,
  a checks list with the six checks) and `examples/report.txt` (the matching text
  report). Static sample artifacts, not generated at test time.
