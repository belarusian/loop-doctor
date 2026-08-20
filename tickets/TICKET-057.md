# TICKET-057 — Extend tests/test_pyproject.py for [project.urls]

## Target
tests/test_pyproject.py (extend)

## Capability
Assert the [project.urls] table is present in pyproject.toml.

## Change
Keep the existing three tests unchanged. Add one new test that:
- Asserts a [project.urls] table is present in pyproject.toml.
- Asserts it contains the repository URL github.com/belarusian/loop-doctor.

## Constraints
- Do NOT modify the existing three tests (test_base_dependencies_are_empty,
  test_git_deps_moved_to_full_extra, test_entry_point_preserved).
- Read pyproject.toml via the existing _text() helper.

## Acceptance
- The new test passes once TICKET-055 lands the [project.urls] block.
- The existing three tests still pass unchanged.
