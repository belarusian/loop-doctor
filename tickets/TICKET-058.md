# TICKET-058 — docs/release.md: short release/packaging doc

## Target
docs/release.md (NEW)

## Capability
A short release/packaging reference doc.

## Change
Create docs/release.md covering:
- How to build: pip install -e . (and pip install -e .[full] for the full extra).
- The dependency boundary: base dependencies are empty; the full extra adds
  spoke-lint and fourseer (for the prompt and run_health checks).
- The loop-doctor entry point (loop_doctor.cli:main).
- The version (0.0.1) and that it is a single source of truth
  (loop_doctor.__version__ == pyproject version, pinned by tests/test_version.py).
- The MIT license.
- The project URLs (Homepage, Repository, Documentation, Issues).

## Constraints
- Keep it short (a page or less).
- No behavior change to any check.

## Acceptance
- The doc exists and accurately reflects pyproject.toml.
