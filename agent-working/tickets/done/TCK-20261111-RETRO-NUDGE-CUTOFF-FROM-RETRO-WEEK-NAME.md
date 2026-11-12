---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261111-RETRO-NUDGE-CUTOFF-FROM-RETRO-WEEK-NAME
phase: done
date: 2026-11-11
tags: [agent-monitoring]
---

# TCK-20261111-RETRO-NUDGE-CUTOFF-FROM-RETRO-WEEK-NAME

## Title
The retro nudge takes its cutoff from the newest RETRO-YYYY-Www week name, not from a file's mtime

## Status
DONE

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
New `tools/agent-monitoring/retro_cutoff.py::latest_retro_week_end_ts()` replaces `_last_dated_retro_mtime()` in `retro_nudge_hook.py`. It takes the newest `RETRO-YYYY-Www.md` by name and returns 00:00 UTC of the day after that week's Sunday, reusing `week_close.week_end`. `RETRO-ALL.md`, names that do not parse and impossible weeks (W99) are ignored; no dated retro gives 0.0. `docs/guides/agent_monitoring.md` now describes the cutoff by week name instead of mtime. The nudge text and the threshold are unchanged.

## Test Summary
`tests/tools/test_retro_cutoff.py`: 5 passed (none; newest week wins; mtimes change nothing; a newer mtime on an older retro does not win; unparsable names ignored). `tests/tools/test_retro_nudge_hook.py`: passes unchanged apart from a comment that named the old helper. Smoke run of the hook with a session id prints the week-close nudge as before.

## Files Changed
tools/agent-monitoring/retro_cutoff.py, tools/agent-monitoring/retro_nudge_hook.py, docs/guides/agent_monitoring.md, tests/tools/test_retro_cutoff.py, tests/tools/test_retro_nudge_hook.py

## Completion Summary
The retro nudge cutoff no longer moves when git touches a retro file; it follows the newest retro's week name.
