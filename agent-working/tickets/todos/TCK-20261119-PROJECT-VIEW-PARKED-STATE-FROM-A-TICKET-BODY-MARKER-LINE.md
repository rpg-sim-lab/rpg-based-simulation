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
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
The Project view ticket (TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED) shipped without Parked. Its step 1 measured that no structured signal exists: only 1 of 223 open tickets has a waits-on line, and none of the 8 Stale tickets has one, so a phrase match would park about a fifth of the backlog (46 of 224). Owner decision (#715, logged 2026-11-19 via lead-planner): file a separate small ticket that adds a ticket-body marker line, `Parked: waits on <TCK-id or PR#N> since <YYYY-MM-DD>`, which the sync reads as a Parked state distinct from Stale. Planners write the line when they park work. Fixture: STALEMATE F1, `TCK-20261030-STALEMATE-BREAK-OVERWRITES-A-PROJECT-MOVE-EVERY-TICK`, which reads Stale on `rpg-nav-stall-on-main` while the work is parked on `rpg-stalemate-nav`.

## Scope
1. The marker: one line starting `Parked: waits on ` in the ticket body, naming a `TCK-` id or `PR#<n>` and a `since` date. It is written by a planner, never inferred. The sync reads only a line-start match, validates the target and the date, and prints a finding for a malformed line without changing the Status.
2. Derivation: a ticket with a valid marker whose target is not Done (ticket) or not merged or closed (PR) shows Parked, in place of Stale and In progress; Done and In review still win, and a ticket Status of BLOCKED still shows Blocked. The marker clears itself when its target is Done, merged or closed, or when the planner removes the line. State the precedence in the docs and test it.
3. A stale marker: decide from the measured age distribution whether a `since` date older than N days adds a finding (not a status change) so an abandoned Parked is visible.
4. The Project's Status select gets a Parked option. The existing doc says replacing Status options clears each item's Status and is refused on a populated Project without `--replace-status-options`. Test the safe path on a scratch Project first, and write the migration order (add option, then `--apply` refills) in the plan. Hard prerequisites, both shown in the dry-run evidence lead-planner sees before any live write: (i) the scratch-Project test result (did adding the option clear item Statuses, yes or no, with the commands run), and (ii) the written migration order. No live Project write without the owner's yes and that evidence.
5. Docs: `docs/guidelines/session_roles/project_sync_dry_run.md` (the marker, the precedence, the finding), `docs/guides/delivery_process.md` (when a planner writes it and removes it), and a pointer in `docs/guidelines/session_roles/functions/planner.md` outside the injected Card (the planner cards are at their token budget).
6. The marker is one line, not a new required section. If it should enter the ticket template in CLAUDE.md, that edit needs the owner's direct yes and is a separate step.

## Out of Scope
- Inferring Parked from phrases, branch age or handover files.
- New required ticket sections or a change to the ticket template.
- Writing the marker into existing tickets, except the F1 live check below.
- The Project view ticket's own fields.

## Acceptance Criteria
1. Synthetic fixture shaped like STALEMATE F1 (an old lane branch whose ticket carries a valid marker naming an open ticket) shows Parked, not Stale. Must-not: the same marker naming a Done ticket shows Stale; a marker mid-line or malformed leaves the Status unchanged and prints a finding; a BLOCKED ticket with a marker shows Blocked; a Done ticket with a marker shows Done.
2. Every derivation reports ran / skipped / errored.
3. A before/after dry run on a named SHA lists the rows whose Status changes. The live check on the real F1 ticket is done by the u24 planner writing the marker after merge, not claimed from ubuntu.
4. Report-only: the sync's exit code and existing fields are unchanged; `--apply` is unchanged except the new option.
5. Scoped tests only; the live Project write needs the owner's yes.

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
Filed by agent-working-planner on lead-planner's relay of an owner decision. The Project view build ships without Parked and records this ticket id in its out-of-scope.

## Test Summary

## Files Changed

## Completion Summary
