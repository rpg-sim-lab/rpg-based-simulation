---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE
phase: open
date: 2026-11-19
tags: [delivery]
---

# TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE

## Title
GitHub Project 1 shows a Parked state, read from a one-line marker a planner writes in the ticket body when work is parked

## Status
INPROGRESS

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
The Project view ticket (TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED) shipped without Parked. Its step 1 measured that no structured signal exists: only 1 of 223 open tickets has a waits-on line, and none of the 8 Stale tickets has one, so a phrase match would park about a fifth of the backlog (46 of 224). Owner decision (#715, logged 2026-11-19 via lead-planner): file a separate small ticket that adds a ticket-body marker line, `Parked: waits on <TCK-id or PR#N> since <YYYY-MM-DD>`, which the sync reads as a Parked state distinct from Stale. Planners write the line when they park work. Fixture: STALEMATE F1, `TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK`, which reads Stale on `rpg-nav-stall-on-main` while the work is parked on `rpg-stalemate-nav`.

## Scope
1. The marker: one line at the START of a line in the ticket body, in three forms: `Parked: waits on <TCK-id> since <YYYY-MM-DD>`, `Parked: waits on PR#<n> since <YYYY-MM-DD>` and `Parked: waits on decision <reference> since <YYYY-MM-DD>` (the decision form, added by agent-working-planner 2026-11-19: the reference is free text and must be non-empty, the date must be valid; a decision target cannot be checked so it never clears itself and clears when the line is removed). Written by a planner, never inferred. The sync reads only a line-start match from origin's copy, validates target and date, and prints a finding for a malformed line without changing the Status.
2. Derivation: a valid marker whose target is open (a ticket not Done, a PR in the open-PR list, or a decision) shows Parked in place of Stale and In progress (and To do); precedence Done, In review, a kept status, Blocked (a ticket Status of BLOCKED), Parked, then the rest. It clears when its ticket is Done, its PR is merged or closed, or the line is removed.
3. Stale marker: **45 days, proposed; only one dated line existed in the corpus on 0b196a142, so it is not measured; revisit when real markers exist.** A `since` older than that adds a finding, never a status change.
4. The Project's Status select gets a Parked option (last). Tested on a scratch Project first (done: see Implementation Notes and the staged investigation); the migration order is written in the docs and in the plan. No live Project write without the owner's yes.
5. Docs: `docs/guidelines/session_roles/project_sync_dry_run.md`, `docs/guides/delivery_process.md`, a pointer in `docs/guidelines/session_roles/functions/planner.md` outside the injected Card.
6. The marker is one line, not a new required section; a CLAUDE.md template change would need the owner's direct yes and is a separate step.

## Out of Scope
- Inferring Parked from phrases, branch age or handover files.
- New required ticket sections or a change to the ticket template.
- Writing the marker into existing tickets, except the F1 live check below.
- The Project view ticket's own fields.

## Acceptance Criteria
1. Synthetic F1 fixture (an old lane branch whose ticket carries a valid marker naming an open ticket) shows Parked, not Stale. Must-nots: a marker naming a Done ticket shows Stale; a malformed or not-line-start marker leaves the Status unchanged and prints a finding; a BLOCKED ticket with a marker shows Blocked; a Done ticket with a marker shows Done; a decision marker needs a non-empty reference and a valid date and never clears itself.
2. Every derivation reports ran / skipped / errored (the `parked:` note).
3. A before/after dry run on a named SHA lists the rows whose Status changes (origin/main 025be2faf: 0, no marker exists). The live check on the real F1 ticket is the u24 planner writing the marker after the code lands, not claimed from ubuntu.
4. Report-only: exit code and existing fields unchanged; `--apply` unchanged except the new option.
5. Scoped tests only; the live Project write needs the owner's yes. The scratch Project's number (2) and its deletion command are in the staged evidence.

## Related Tickets
- TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED (shipped without Parked; this is its deferred part)
- TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK (fixture)
- TCK-20261119-FILED-TICKETS-ARE-SCANNED-FOR-OVERLAP-WITH-OPEN-TODOS (sequencing: this ticket is dispatched after it)
- overlap scan: 5 hits, none duplicate (tools/open_ticket_overlap.py on this draft: the Project view ticket 57.9 is the parent cited above; the two other tickets named above are cited; TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION 21.5, TCK-20261117-A-BLOCKED-WALKER-HAS-NO-MEMORY-OF-ITS-DETOUR-HEADING 21.0 and TCK-20261118-A-SUBJECT-WITH-A-STANDING-HELP-NEED-RE-DECIDES-SOLO-EVERY-TICK 19.1 share only generic words)

## Related Docs
- `docs/guidelines/session_roles/project_sync_dry_run.md`

## Related Stored Artifacts
- none yet

## Related Code Areas
- `tools/sessions/project_sync.py` (`derive_status`, `parse_copy`)
- `tools/sessions/project_client.py`, `registries/session_project.yaml`
- `tests/tools/`

## Assumptions / Open Questions
- Whether adding a Status option clears item Statuses on a populated Project: untested, to be tried on a scratch Project.
- The age threshold for a stale marker is unmeasured.
- Sequencing: dispatched after the overlap-scan ticket; RPG first.

## Durable state, lifecycle and clocks
Parked is derived on each sync from the ticket body and the target's state; it adds no stored state. The marker line is written by a planner and ends when the target is Done, merged or closed, or when the line is removed. The `since` date is informational and only drives the optional age finding.

## Implementation Notes
Scratch-Project test (owner-approved, #715 7011473532): Project 2 in org rpg-sim-lab (`scratch-parked-status-test`, id PVT_kwDOFTLAWc4BsWS4, https://github.com/orgs/rpg-sim-lab/projects/2), 9 draft items on the six options. `init_fields` (the real code path, no `--replace-status-options`) appended Parked: every option id and every item Status unchanged (8 of 8); the control (the same options sent without ids) cleared 8 of 8. Deletion by the owner: `gh project delete 2 --owner rpg-sim-lab`, or through GraphQL `mutation{deleteProjectV2(input:{projectId:"PVT_kwDOFTLAWc4BsWS4"}){clientMutationId}}`. Project 1 was not touched.
Built on agent-working-parked-marker (base 0b196a142); decisions by agent-working-planner 2026-11-19: a decision form `Parked: waits on decision <reference> since <date>` (a decision target never clears itself), origin's copy only, 45-day stale-marker finding as a PROPOSAL, precedence Done, In review, kept status, Blocked, Parked, then the rest. Code, tests and docs are written; the migration order is drafted in staging; the scratch-Project result (and the owner's approval to create a Project) is the hard prerequisite before any live write or merge ask.
Filed by agent-working-planner on lead-planner's relay of an owner decision. The Project view build ships without Parked and records this ticket id in its out-of-scope.

## Test Summary

## Files Changed

## Completion Summary
