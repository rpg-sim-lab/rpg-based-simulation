---
status: active
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261115-PROJECT-SYNC-FILED-DATE-AND-BACKLOG-VIEW
phase: open
date: 2026-11-15
tags: [planning, delivery]
---

# TCK-20261115-PROJECT-SYNC-FILED-DATE-AND-BACKLOG-VIEW

## Title
`project_sync.py`: a `Filed` date field from each ticket's frontmatter date, so the owner's Backlog view can show the open-ticket pile by Domain, Priority and age

## Status
OPEN

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
Owner concern (#715 6883358041, exact): "the todos tickets are growing much, you should consider that when completed the project board".
Main has about 140 loose todos plus 7 epic folders, and inprogress/ tickets sit there from October. agent-working-planner-u24 answered
through lead-planner-u24, and the owner chose "File + dispatch after P3b" (#715 6883401913).
- A Backlog view, filtered to To do, grouped by Domain and sorted by Priority, needs no code. GitHub shows the count per group.
- Age needs one field. This ticket adds it.
- Rejected:
  - a new "stale todo" Status, because `Stale` already means "branch untouched for `stale_branch_days`";
  - backlog counts copied into the heartbeat item or `project_facts.md`, because the grouped view already counts and a copy drifts.
- Triage of the open tickets themselves is per domain, the owner's call, and not this ticket.

**Dispatch only after P3b (TCK-20261115-PROJECT-SYNC-ALL-LANES) merges.** It can run before, or alongside, P3c.

## Scope
1. **Field.** `--init` creates a DATE field `Filed`. `project_client` gains a date-value write (`updateProjectV2ItemFieldValue` with
   `date`). An empty value clears the field.
2. **Value.** `Filed` is the ticket's frontmatter `date:` (YYYY-MM-DD) from the copy the content rule picks.
   - If the date is missing or not a valid date, the field is left empty and a finding is added.
   - The keep-current rule (another host's lowest tag) keeps the current value, as for the other content fields.
3. **Hash.** `Filed` joins the hash fields as hash v4, using the existing version mechanism. The first run after this lands rewrites
   every item once: about 180 items, the Filed value plus Sync hash. It must report no hand edits.
4. **Docs.** In `project_sync_dry_run.md`:
   - the field;
   - the owner's Backlog view, as a UI step: filter `status:"To do"`, group by Domain, sort by Priority, then Filed. For age, a filter
     such as `filed:<@today-30d`;
   - a limits line saying that age is the filing date, not the last activity.
5. **Tests, no network** (about 4):
   - Filed from the frontmatter date;
   - a bad or missing date gives empty plus a finding;
   - the v4 migration gives no hand edits;
   - init creates a DATE field, and a second init does nothing.

## Out of Scope
- Triage, closing or moving any ticket.
- A new Status value.
- Counts stored anywhere.
- The timer: P3c.

## Acceptance Criteria
1. Scope items 1-5 are built, and the scoped tests pass.
2. Live:
   1. a dry run first, with the expected about 180 Filed and hash updates and 0 archives;
   2. then `--init` and `--apply`, run in the owner's or lead's terminal (a seat's `--apply` is blocked by the permission check),
      gated on that plan;
   3. then a final dry run that must show nothing to do.
3. The owner saves the Backlog view. That is an owner UI step, named in the PR body.

## Related Tickets
- TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW (parent)
- TCK-20261115-PROJECT-SYNC-ALL-LANES (P3b, goes first)
- TCK-20261115-PROJECT-SYNC-HOST-TIMER (P3c)

## Related Docs
- `docs/guidelines/session_roles/project_sync_dry_run.md`

## Related Stored Artifacts

## Related Code Areas
- `tools/sessions/project_sync.py`, `tools/sessions/project_client.py`, `tests/tools/test_session_project_sync*.py`, `tests/tools/test_project_client.py`

## Assumptions / Open Questions
- **Simpler-fix check (6698958617):** with no code, the Backlog view can still group and count by Domain and Priority, but it cannot
  sort or filter by age. The field costs about 30 lines, 4 tests and one paced rewrite of about 180 items (about 3 min).
- GitHub's date filter syntax (`@today-30d`) is to be confirmed in the UI. The doc names it, with a fallback of sorting by Filed.
- Gate drift: a plan gated on an exact diff moves when another seat renames a local branch (seen in P3b round 2). Running straight
  after the OK is the working practice. A count-based gate is not proposed here.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
