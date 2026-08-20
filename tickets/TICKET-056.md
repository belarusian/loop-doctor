# TICKET-056 — tests/test_version.py: version single-source-of-truth

## Target
tests/test_version.py (NEW)

## Capability
Pin loop_doctor.__version__ to the pyproject version so the two can never drift.

## Change
Create tests/test_version.py with tests that:
- Parse the [project] version from pyproject.toml with the regex
  ^version\s*=\s*"([^"]+)" in re.MULTILINE mode.
  Do NOT import tomllib (not in the py3.10 stdlib CI uses).
- Assert the parsed version equals loop_doctor.__version__.
- Assert main(["--version"]) returns 0 and its stdout contains
  f"loop-doctor {__version__}".
- Assert the version matches ^\d+\.\d+\.\d+$ (semver-like, three numeric parts).

## Constraints
- No tomllib import.
- Capture stdout with capsys (or io.StringIO + contextlib.redirect_stdout).
- Read __version__ from loop_doctor, not a hardcoded literal, where the test
  asserts the relationship.

## Acceptance
- All tests pass with the current version 0.0.1.
- If the pyproject version and __version__ diverge, the test fails.
