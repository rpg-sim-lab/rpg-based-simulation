---
status: historical
layer: ticket
authority: P1
audience: agent
ticket_id: TCK-20261115-PROJECT-SYNC-FILED-DATE-AND-BACKLOG-VIEW
phase: done
date: 2026-11-15
tags: [planning, delivery]
---

# TCK-20261115-PROJECT-SYNC-FILED-DATE-AND-BACKLOG-VIEW

## Title
`project_sync.py`: a `Filed` date field from each ticket's frontmatter date, so the owner's Backlog view can show the open-ticket pile by Domain, Priority and age

## Status
DONE

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
   - a limits line saying that age is the filing date, not the last activity;
   - a limits line saying that a merged ticket gets a Done item only while some host's worktree still has its branch checked out (seen in
     P3b AC3.5 on ubuntu, #917). The Done lane is therefore not a full list of recent closes. This is a doc line only, with no code change.
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
- `project_client.py`: `set_date`, `create_date_field`, `DATE_FIELDS`; `list_items` reads `ProjectV2ItemFieldDateValue`; `init_fields` creates `Filed` (a wrong type is refused before any write); `Filed` is last in `VALUE_ORDER` and written as a date or cleared when empty.
- `project_sync.py`: `filed_date()` (strict `YYYY-MM-DD`, valid calendar date, else empty plus a `Filed left empty` finding); `Filed` joins the hash as v4 (`HASH_FIELDS_V3` kept); the keep-current rule keeps the current value.
- Doc: `docs/guidelines/session_roles/project_sync_dry_run.md`, section "Filed date and the Backlog view".

## Test Summary
`tests/tools/test_session_project_sync_filed.py` (5 tests) plus fixture updates in 4 project-sync test files: 164 passed (scoped, no network). Live (lead's terminal, #715 6883401913): `--init` created Filed, second `--init` all "left alone"; plan matched the planner's OK; `--apply` rc 0, 634 steps, 04:51:33Z to 05:06:55Z; final dry run "nothing to do", 0 updates, 0 hand edits; failed_streak 0; no token leak.

## Files Changed
`tools/sessions/project_client.py`, `tools/sessions/project_sync.py`, `tests/tools/test_session_project_sync_filed.py` (new), `tests/tools/test_project_client.py`, `tests/tools/test_session_project_sync.py`, `tests/tools/test_session_project_sync_all_lanes.py`, `tests/tools/test_session_project_sync_second_host.py`, `docs/guidelines/session_roles/project_sync_dry_run.md`, `docs/REGISTRY.yaml`, ticket, monitoring shards.

## Completion Summary
**Load (lead's terminal, #715 6883401913):** `--init` created `Filed` and a second `--init` was all "left alone". `--apply` ran 04:51:33Z to 05:06:55Z: rc 0, **634 steps**, "nothing left". That is more than the ~400 estimated because every update writes Source and Sync hash as well as Filed (3 steps for each of 181 updates = 543), and the 4 new-since-P3b creates, the other changed fields (status, branch, PR, host facts) and the heartbeat make up the rest. Final dry run: "nothing to do", 0 updates, 0 hand edits (so the DATE read-back equals the YYYY-MM-DD we write); last-run.json rc 0, failed_streak 0; no token leak.

**Owner UI step (not code):** save the Backlog view on https://github.com/orgs/rpg-sim-lab/projects/1: table view, filter `status:"To do"`, group by Domain, sort by Priority then Filed; for age add `filed:<@today-30d` (sort by Filed if the UI rejects it).

The Project has a `Filed` date field filled from each ticket's frontmatter date, under hash v4, loaded on 183 items with no hand edits. The owner's Backlog view is a UI step (status "To do", group by Domain, sort by Priority then Filed), named in the PR body and the doc. Two limits lines added: Filed is the filing date, not activity; the Done lane needs a worktree on the branch.
