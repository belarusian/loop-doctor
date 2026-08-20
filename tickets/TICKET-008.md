# TICKET-008 — Report lacks Report.add(check) and a stable summary() line shared by both renderers

## Title
`loop_doctor/report.py` `Report` has no `add(check)` method and no stable
`summary()` line (counts by status). The two renderers (`render_text`,
`render_json`) each re-derive the verdict and iterate checks independently, so a
single shared summary is impossible and the renderers can drift.

## Evidence
- `loop_doctor/report.py:40` `Report` is a dataclass with only a `checks` list and
  the `verdict`/`go` properties. There is no `add` method; callers must build the
  full list up front (`Report(checks=[...])`).
- `loop_doctor/report.py:63` `render_text` and `loop_doctor/report.py:79`
  `render_json` each compute `report.verdict` and iterate `report.checks` on their
  own. Neither exposes a per-status count, and there is no shared `summary()`.
- Cycle 2 briefing "What to Build" row `loop_doctor/report.py`: "Add
  Report.add(check) and a stable summary() line (counts by status) used by both
  renderers; keep byte-stable output."
- `tests/test_report.py` builds reports only via `Report(checks=[...])`; there is
  no test for incremental `add` or for a summary count.

## Impact
- The registry (`checks.py`) and the CLI want to build a report incrementally
  (one check at a time) rather than pre-assembling a list; without `add` they must
  mutate the list directly, which is error-prone and not part of the model's API.
- A per-status count (pass/fail/warn/skip) is the natural "summary" an operator
  wants, but neither renderer produces it, so adding it later would change the
  byte-stable output contract.
- The two renderers duplicating verdict/iteration logic risks them diverging.

## Suggestion
In `loop_doctor/report.py`:
- Add `Report.add(check: Check) -> None` that appends to `self.checks` (and returns
  `self` or `None` consistently).
- Add `Report.summary() -> str` returning a single stable line with counts by
  status in a fixed order (e.g. "pass=1 fail=0 warn=1 skip=1"), deterministic and
  independent of insertion order.
- Keep `render_text` and `render_json` byte-stable: do NOT change their existing
  output bytes; the summary is additive (a new method), not a change to the
  existing rendered lines.
Add deterministic tests: `add` grows the report and the verdict tracks it;
`summary()` counts are correct and stable across repeated calls; existing
`render_text`/`render_json` output is unchanged (byte-stable).
