# TICKET-044 — Document the full CLI and add release metadata to pyproject.toml

## Title
`README.md` must document the full CLI: the `--check NAME` flag, the new
`--list-checks` flag, the exit-code contract (0 go / 1 no-go / 2 usage error),
and the JSON output shape (verdict, checks, summary). `pyproject.toml` must
gain release metadata: classifiers (Python 3.10/3.11/3.12, OS Independent,
Console, MIT), keywords, and author. Do NOT change the version, the dependency
boundary (base deps empty, full extra), or the entry point.

## Evidence
- `README.md` documents only `loop-doctor check <project-dir> [--json]`; it
  omits `--check`, `--list-checks`, the exit-code contract, and the JSON shape.
- `pyproject.toml` has no `author`, `keywords`, or `classifiers`; version is
  `0.0.1`, `dependencies = []`, entry point `loop-doctor = "loop_doctor.cli:main"`.
- `tests/test_pyproject.py` pins the empty base deps, the full extra, and the
  entry point (all must remain intact).
- Cycle 9 briefing "What to Build" rows `README.md` and `pyproject.toml`.

## Impact
- Users cannot discover the flags / exit codes / JSON shape from the docs; the
  package lacks standard release metadata.

## Suggestion
- Extend the README Usage section with `--check`, `--list-checks`, an
  exit-code table, and the JSON shape; keep it accurate to what is implemented.
- Add `author`, `keywords`, and `classifiers` to `[project]` in
  `pyproject.toml`; leave version, `dependencies = []`, the `full` extra, and
  the entry point unchanged.
