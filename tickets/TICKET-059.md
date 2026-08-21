# TICKET-059: new check module loop_doctor/ci.py

## Capability
A `ci_check(project_dir: Path) -> Check` (name="ci") following the existing
check-module pattern (report Check/Status, detail string). It verifies the
project's main-branch head commit has green GitHub Actions CI.

## Decision order
1. `git -C <dir> rev-parse --is-inside-work-tree` fails, OR
   `git -C <dir> remote get-url origin` fails/empty -> SKIP, detail
   "not a git repo with origin".
2. Parse owner/name from the origin URL. Only `https://github.com/{owner}/{name}`
   (optional trailing `.git`) and `git@github.com:{owner}/{name}.git` are
   supported; anything else -> SKIP, detail "non-GitHub remote".
3. `git -C <dir> fetch origin main --quiet` then `git -C <dir> rev-parse
   origin/main` -> head SHA. If fetch fails but the local origin/main ref still
   resolves, proceed using it and note it in the detail. If origin/main cannot
   be resolved at all -> SKIP, detail naming the rev-parse failure.
4. `gh api repos/{owner}/{name}/commits/{sha}/check-runs` (JSON) and evaluate:
   - zero check runs -> SKIP, detail "no check runs for {short-sha}".
   - any run with status != "completed" -> FAIL, detail
     "CI in progress for {short-sha}: {done}/{total} completed".
   - any run with conclusion in {failure, cancelled, timed_out, action_required}
     -> FAIL, detail "CI red at {short-sha}: {check names}".
   - all runs completed with conclusion in {success, neutral, skipped} -> PASS,
     detail "CI green at {short-sha}".
5. `gh` missing OR any git/gh subprocess failure OR invalid JSON -> SKIP with
   the stderr tail in detail. An indeterminate environment must NOT hard-block
   the verdict — surface it as SKIP (mirrors the prompt check's
   optional-dependency SKIP convention).

## Mockable seam (rule 4)
Route every git/gh invocation through a single module-level helper
`_run(cmd: list[str]) -> subprocess.CompletedProcess` so tests patch it with
`patch.object(loop_doctor.ci, "_run", ...)`. The helper must normalize a missing
binary (FileNotFoundError) to a non-zero returncode result (e.g. returncode=127,
stderr "<cmd>: command not found") so a missing `gh` is a SKIP, not an exception.
Tests never touch the network or real gh.

## Acceptance
- `ci_check` returns a `Check` with name "ci".
- All five decision branches covered.
- No network, no real gh in tests.
