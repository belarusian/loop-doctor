# TICKET-055 — Add [project.urls] block to pyproject.toml

## Target
pyproject.toml

## Capability
Complete the PEP 621 release metadata: add the missing [project.urls] table.

## Change
Add a [project.urls] table (immediately after the [project.optional-dependencies]
block, before [project.scripts]) with exactly these four keys:
- Homepage = https://github.com/belarusian/loop-doctor
- Repository = https://github.com/belarusian/loop-doctor
- Documentation = https://github.com/belarusian/loop-doctor/blob/main/docs/architecture.md
- Issues = https://github.com/belarusian/loop-doctor/issues

## Constraints
- Do NOT change name, version, description, readme, requires-python, authors,
  keywords, classifiers, dependencies, the full extra, or the [project.scripts]
  entry point.
- This is the ONLY source change in the cycle. No file under loop_doctor/ changes.
- After editing, validate the editable build locally:
  /usr/bin/python3 -m pip install -e . --no-deps
  (a pyproject metadata change can pass the local gate yet break the CI build).

## Acceptance
- pyproject.toml parses and the editable build succeeds.
- The [project.urls] table is present with the four keys above.
- Gate stays green: pytest, ruff, mypy.
