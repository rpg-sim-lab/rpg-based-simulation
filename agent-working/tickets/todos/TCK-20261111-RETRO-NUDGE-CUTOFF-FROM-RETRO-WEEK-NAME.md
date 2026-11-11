---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261111-RETRO-NUDGE-CUTOFF-FROM-RETRO-WEEK-NAME
phase: open
date: 2026-11-11
tags: [agent-monitoring]
---

# TCK-20261111-RETRO-NUDGE-CUTOFF-FROM-RETRO-WEEK-NAME

## Title
The retro nudge takes its cutoff from the newest RETRO-YYYY-Www week name, not from a file's mtime

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
`tools/agent-monitoring/retro_nudge_hook.py::_last_dated_retro_mtime()` uses the largest
`st_mtime` among the local `RETRO-*.md` files as the "last retro" cutoff. Git sets mtime whenever it
writes a file (a checkout, merge or branch switch in a worktree), so any sync that touches a retro
moves the cutoff to that moment. The count of DONE runs since the last retro then drops, and the
nudge goes quiet even though no new retro exists. The value also differs between worktrees for the
same commit. Found while reviewing #860.

## Scope
- Derive the cutoff from the newest `RETRO-YYYY-Www.md` name: the end of that ISO week (Sunday
  24:00 UTC). This matches how the week close defines a finished week. Ignore `RETRO-ALL.md` and
  names that don't parse. No dated retro still means cutoff 0.
- Rename the helper to say what it returns.
- Tests: a touched old retro file doesn't move the cutoff; the newest week wins over a newer
  mtime; an unparsable name is ignored; no retros gives 0.

## Out of Scope
- When retros are due (the cadence rule is unchanged), and any change to the nudge text.

## Acceptance Criteria
1. The cutoff for a fixed set of retro file names is the same whatever the files' mtimes.
2. The existing nudge tests pass unchanged, or are updated only where they relied on mtime.

## Related Tickets

## Related Docs
- docs/guides/agent_monitoring.md (retro cadence)

## Related Stored Artifacts

## Related Code Areas
- tools/agent-monitoring/retro_nudge_hook.py, tests/tools/ (retro nudge tests)

## Assumptions / Open Questions
- A retro named for week W covers activity up to the end of W, so a run that started later counts
  toward the next nudge.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
