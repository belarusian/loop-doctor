# TICKET-064: docs + CHANGELOG + real validation

## Capability
- `docs/architecture.md` gains capability 6 (the ci check) in the same section
  shape as the other five: purpose, decision order, the `_run` seam, and the
  SKIP-on-indeterminate convention.
- `README.md` check list updated to include `ci` (seven checks).
- `CHANGELOG.md` entry for the CI CHECK, following the version
  single-source-of-truth rule from Cycle 12 (no hardcoded version that
  disagrees with `loop_doctor/__init__.py`; use an `[Unreleased]` section).
- REAL validation on this machine (record the actual output in the Cycle 14
  block):
  - `loop-doctor check ~/AI/loop-doctor/proj` ends GO with ci PASS.
  - `loop-doctor check ~/AI/fleet` — record what the ci check says there
    (record, do NOT fix fleet).
  - Real validation needs `git` + `gh` on PATH and a network connection to the
    GitHub API; it is NOT part of the mocked test suite.

## Acceptance
- architecture.md, README.md, CHANGELOG.md updated and consistent.
- Real validation output captured verbatim in the Cycle 14 log block.
