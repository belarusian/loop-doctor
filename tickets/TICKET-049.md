# TICKET-049 — Exhaustive edge-case tests for loop_doctor/project.py

## Title
Add exhaustive edge-case and branch-coverage tests to tests/test_project.py so
every branch of loop_doctor/project.py is pinned, without changing any source
behavior. Cover: resolve_ai_dir from the ai dir, from the proj dir, and from
the parent (existing + the ai-dir-named case); resolve_proj_dir from the proj
dir and from the parent; the 3-file-set resolution (existing); a non-existent
path; a file (not a dir) passed where a dir is expected; the _first_match
helper (sorted determinism, non-file entries ignored, no match); the
_parse_seed_ref helper (no marker, marker with no fence, empty fence, leading
blank lines inside the fence, tilde fence); and the foundation check
detail/verdict (PASS "ai dir {ai_dir}", FAIL naming what is missing).

## Evidence
- loop_doctor/project.py has ThreeFiles, resolve_ai_dir, resolve_proj_dir,
  _first_match, _parse_seed_ref, locate_three_files, and resolve_project.
- resolve_ai_dir returns project_dir.parent / "ai" when the dir is named proj,
  else project_dir / "ai". resolve_proj_dir returns project_dir when named
  proj, else project_dir / "proj". _first_match returns the first sorted file
  matching a pattern, or None. _parse_seed_ref finds the first THE SEED line,
  the next fence, and the first non-empty line inside it.
- tests/test_project.py has 7 tests; it does not cover resolve_proj_dir, the
  ai-dir-named input, a file-not-dir input, _first_match determinism, the
  _parse_seed_ref edge cases, or the foundation check detail/verdict.

## Impact
- resolve_proj_dir, the ai-dir-named and file-not-dir inputs, _first_match
  determinism, the _parse_seed_ref edge cases, and the foundation check
  detail/verdict are not pinned.

## Suggestion
- Add tests for resolve_proj_dir (from the proj dir and from the parent).
- Add a test that resolve_ai_dir on a dir named ai returns ai/ai (the
  parent-treatment branch).
- Add a test that a regular file passed as the project dir is handled (the
  is_dir() guard in _first_match returns None).
- Add tests for _first_match: multiple matches -> first sorted; a directory
  matching the pattern is ignored; no match -> None.
- Add tests for _parse_seed_ref: no THE SEED marker -> None; marker with no
  following fence -> None; empty fence -> None; leading blank lines inside the
  fence are skipped; a ~~~ fence is accepted.
- Add foundation-check tests (via loop_doctor.checks.run_one("foundation", ...))
  asserting the PASS detail f"ai dir {ai_dir}" and the FAIL detail naming the
  missing file(s).
