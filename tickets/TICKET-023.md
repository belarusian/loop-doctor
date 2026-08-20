# TICKET-023 — Tests: bash check PASS (no drivers / valid driver) and FAIL (syntax error)

## Title
Deterministic, network-free tests are needed for the new `bash` check. The check
must PASS when there are no `.sh` drivers, PASS when a well-formed `.sh` driver
parses cleanly, and FAIL (with a detail naming the offending script) when a `.sh`
driver has a syntax error. The `.sh` drivers are built under `tmp_path` (write a
valid script and an invalid one).

## Evidence
- `loop_doctor/bash_check.py` (TICKET-020) exposes `bash_check(project_dir) ->
  Check` named `bash`. It resolves the `proj` dir via
  `loop_doctor.project.resolve_proj_dir`, finds `*.sh` files directly in the `proj`
  dir (sorted), and runs `bash -n <script>` on each.
- `bash -n` is a parse-only syntax check (no execution); a non-zero `returncode`
  is a syntax failure. It is available at `/usr/bin/bash` on this host.
- There are currently NO `.sh` drivers at the project root, so the empty case must
  PASS (a project with no shell drivers is not broken).
- Cycle 5 briefing "What to Build" row `tests/`: "bash PASSes when there are no
  `.sh` drivers; PASSes when a well-formed `.sh` driver parses cleanly; FAILs (with
  the right detail naming the script) when a `.sh` driver has a syntax error (e.g.
  an unclosed `if` or a stray `then`)".

## Impact
- The new check would be untested; a regression in the empty-case handling or the
  FAIL detail would go unnoticed.

## Suggestion
- Add `tests/test_bash_check.py`:
  - PASS when there are no `.sh` drivers (detail mentions "no .sh drivers").
  - PASS when a well-formed `.sh` driver parses cleanly.
  - FAIL (with a detail naming the offending script) when a `.sh` driver has a
    syntax error (e.g. an unclosed `if`).
  - Build the `.sh` drivers under `tmp_path` (write a valid script and an invalid
    one). Tests must be deterministic and network-free.
