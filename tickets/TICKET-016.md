# TICKET-016 — Prompt check must filter to invocation findings only (exclude missing_tool)

## Title
`spoke_lint.diff_prompt` returns BOTH invocation findings (`missing_script`,
`unknown_flag`, `missing_required`) AND gate-command findings (`missing_tool`). The
gate-command stage treats any command-like line in the prompt as a gate tool and flags
it when it is not on `PATH`. A real runner prompt is prose-heavy (fenced blocks,
numbered lists, sentences), so `diff_prompt` emits many false-positive `missing_tool`
findings on it. The PROMPT LINT capability is specifically about validating *spoke
invocations against argparse signatures*, so the check must filter to invocation
findings only and ignore `missing_tool`.

## Evidence
- `spoke_lint/diff.py` `diff_prompt` appends `diff_gate_commands(text, path)` findings
  after the invocation findings.
- Running `spoke_lint.diff_prompt` on the real loop-doctor runner prompt yields 18
  findings, ALL of kind `missing_tool` (e.g. "(You", "```", "Read", "1", "GO."), and
  ZERO invocation findings (the single `auditor-implementation.py --goal ... --max-steps
  25` invocation is valid).
- Without the filter, the real project would FAIL the prompt check and the aggregate
  verdict would regress to NO-GO, breaking the existing GO end-to-end tests.

## Impact
- If the check used the raw `diff_prompt` output, the real loop-doctor project (and any
  prose-heavy runner prompt) would be reported NO-GO even though its spoke invocations
  are correct.

## Suggestion
- In `prompt_check`, compute `findings = spoke_lint.diff_prompt(text, spokes_dir)` and
  keep only those whose `kind` is in `{"missing_script", "unknown_flag",
  "missing_required"}`.
- PASS when the filtered list is empty; FAIL with a detail built from the filtered
  findings (e.g. one `"<kind>: <flag>"` per finding, joined).
- `spokes_dir` is the directory the prompt's spoke invocations point at (resolve it
  from the prompt's `~/Research/four/examples/spokes` references, or accept a default).
