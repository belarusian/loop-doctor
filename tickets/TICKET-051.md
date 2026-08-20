# TICKET-051 — Add the MIT LICENSE file

## Title
Add a `LICENSE` file containing the MIT license text so the declared license
classifier is backed by an actual license file in the repo.

## Evidence
- `pyproject.toml` declares the classifier `"License :: OSI Approved :: MIT License"`.
- `pyproject.toml` declares `authors = [{ name = "belarusian" }]`.
- No `LICENSE` file exists at the repo root.

## Impact
- The package claims an MIT license in its metadata but ships no license text.

## Suggestion
- Create `LICENSE` at the repo root with the standard MIT license text, copyright
  line `Copyright (c) 2026 belarusian`.
