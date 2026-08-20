# TICKET-046 — Exhaustive edge-case tests for loop_doctor/prompt.py

## Title
Add exhaustive edge-case and branch-coverage tests to tests/test_prompt.py so
every branch of loop_doctor/prompt.py is pinned, without changing any source
behavior. Cover: PASS on a well-formed runner prompt (exact detail
"ai dir {ai_dir}"); FAIL on an unknown flag (existing); FAIL on a missing
script (existing); FAIL on a missing required flag; SKIP when spoke_lint is
absent (guard the real-dep cases with pytest.importorskip and keep the
mocked-absence case); the detail-string format for multiple findings
("; ".join of kind: flag); multiple invocations in one prompt; and the
_resolve_spokes_dir / _invocation_findings / _format_findings helpers.

## Evidence
- loop_doctor/prompt.py has _INVOCATION_KINDS = frozenset({"missing_script",
  "unknown_flag", "missing_required"}), _SPOKES_DIR_RE = re.compile(r"(\S*/spokes)"),
  _DEFAULT_SPOKES_DIR = Path("spokes"), _resolve_spokes_dir,
  _invocation_findings, _format_findings, and prompt_check.
- prompt_check FAILs "missing: runner prompt" when the prompt is not located;
  SKIPs "spoke-lint not installed" when spoke_lint is not importable; FAILs
  "unreadable runner prompt" on OSError/UnicodeDecodeError; PASSes
  f"ai dir {ai_dir}" when there are no invocation findings; else FAILs
  _format_findings(findings).
- tests/test_prompt.py has 5 tests; it does not pin the PASS detail, the
  missing-required case, the multi-finding detail format, multiple invocations,
  or the helper functions.

## Impact
- The PASS detail, the missing-required branch, the multi-finding detail
  format, and the helper functions are not pinned; regressions in any of them
  would not be caught.

## Suggestion
- Add a PASS test asserting the exact detail f"ai dir {ai_dir}".
- Add a FAIL test for a missing required --goal flag (assert missing_required).
- Add a FAIL test with two findings and assert the exact "; "-joined detail.
- Add a test with two invocations in one prompt (one valid, one invalid).
- Add unit tests for _resolve_spokes_dir (with and without a /spokes reference,
  ~ expansion), _invocation_findings (drops missing_tool), and _format_findings.
- Guard the real-dep FAIL/PASS tests with pytest.importorskip("spoke_lint").
