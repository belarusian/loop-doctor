# TICKET-052 — Add a CHANGELOG.md

## Title
Add a `CHANGELOG.md` recording the per-cycle changes, so the project's release
history is discoverable without reading git log.

## Evidence
- No `CHANGELOG.md` exists at the repo root.
- `git log --oneline` shows ten feature cycles, each a merge + feat commit.
- The version is still `0.0.1` across all cycles, so the version number carries no history.

## Impact
- A newcomer or downstream user cannot see what changed between releases without
  reading git history and the tickets/ dir.

## Suggestion
- Create `CHANGELOG.md` using Keep a Changelog format, with a `[0.0.1]` entry
  summarizing the 12-cycle build: the six checks, the go/no-go aggregate + exit codes,
  the CLI surface, and the hardening.
