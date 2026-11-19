---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED
phase: done
date: 2026-11-19
tags: [delivery]
---

# TCK-20261119-PROJECT-VIEW-SEAT-COLLABORATORS-LINK-BY-COMMIT-SUBJECT-AND-PARKED

## Title
GitHub Project 1 shows the holding seat, the collaborating seats and a Parked state, so the owner can track a ticket there instead of asking the leads

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner (#715 7003649308): "if it show the ticket status and I can track them, instead of keep asking you, it a better approach ... even better if I can know what seat holding or join collaboration on a specific tickets". Relayed by lead-planner, from lead-planner-u24's live read of Project 1 (328 items) and a `project_sync` dry run that said "nothing to do": the sync is current and the derivation is what is wrong. Three live cases (the fixtures for this ticket):
- TCK-20261118-A-SERVICE-PAYMENT-WITH-NO-PAYEE-DESTROYS-COIN shows "To do" with no seat; rpg-implementer-3 is working it on `rpg-coin-sink`.
- STALEMATE F1 shows Stale on `rpg-nav-stall-on-main`; it is parked on `rpg-stalemate-nav`.
- #965 and #781 show "rpg (seat not recorded)"; rpg-implementer-2 holds #965.
Causes, as diagnosed by lead-planner-u24 (not re-verified by the planner; step 1 below re-checks them): (1) the Seat comes only from launcher leases and the lane worktrees under `/mnt/data2/rpg-wt/*` have none; (2) a branch links to a ticket only if it changes the ticket file, and ticket ids in commit subjects are ignored; (3) there is no collaborator field; (4) there is no parked or waits-on state, so parked work reads as Stale.

## Scope
Report-only: `tools/sessions/project_sync.py` derivation plus the Project fields it writes. Tickets are written exactly as today.
1. Re-measure the four causes on a named ref and SHA (live Project read plus a dry run), and count how many of the 328 items each cause affects, before building.
2. (a) Seat per lane worktree: record the seat when the worktree is created. This is the parked hotfix `TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT` ("revisit after P1b" is now due): do it there, reuse the record `launch.py --worktree` writes, and do not guess seats from branch names (its recorded out-of-scope). The launcher hook is agent-working's.
3. (b) Link a branch to a ticket by the ticket ids in its own commit subjects since the merge base, as well as by a changed ticket file. A subject that merely cites a ticket (as `pr_render` already treats "cited, not closed") must not move a ticket to In progress: decide and test the rule.
4. (c) An "Involved" field (text, seats): seats that authored commits naming the ticket, plus seats that posted PR or #715 comments starting `<seat>, <date>:` about it. Reads go through the existing read-only `gh api repos/...` guard; no new write path.
5. (d) "Blocked by" from the ticket's Related Tickets / waits-on line, and a Parked state distinct from Stale (a branch that is old because it is waiting on something is Parked, not Stale). Define what marks a ticket parked from data already in the ticket or a branch, and say what a wrong guess costs.
   Form of (a): a CLI that takes `(worktree, seat)` and writes the same record `launch.py --worktree` writes. Never a hand edit of the record.
   Both hosts are in scope (owner #715 7003719833: "both hosts are fine"). Each host's sync writes only its own facts, so ubuntu writes ubuntu's records.
   Backfill step: after the merge, a u24 seat runs the CLI once for the ~15 lane worktrees under `/mnt/data2/rpg-wt/*` on u24. Known: `m1kind5` = rpg-implementer-2, `coinsink` = rpg-implementer-3; rpg-planner confirms the rest at backfill time. The CLI refuses an unknown seat and an existing record for another seat. This overrides the hotfix's "no back-fill" out-of-scope line for this one-time step only.
   (e) A "Hotspot" field (text), owner decision #715 7003894694 (concern from lead-planner-u24, #715 7003841278): of the `src/` files in the ticket's own `## Related Code Areas` (which `project_sync` already reads for Domain via `code_area_paths`), the one cited by the most open tickets on origin/main; empty when the ticket cites no `src/` file or no file is cited by 2 or more tickets, and ties break by path order. The aim is to make clusters visible so a lane can take a file's tickets as one package. lead-planner-u24's numbers, unchecked by the planner: over the 139 rpg To-dos, `intelligence.py` is cited 15 times, `tactical.py` 13, `core/state.py` 11, `scorers.py` and `kernel.py` 7 each; 50 files are cited by 2 or more tickets; 150 of 157 rpg To-dos have no epic. Step 1 re-measures these. Done tickets are not counted. Derived on each run, no stored state.
6. A sync-hash version bump for the new fields, the new fields created by `--init`, and `docs/guidelines/session_roles/project_sync_dry_run.md` updated.

## Out of Scope
- Parked is deferred to TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE (ticket-body marker line; dispatched after the overlap-scan ticket).
- Changing how tickets are written or adding ticket fields.
- Guessing a seat from a branch name or a static map.
- Back-filling records by any route other than the one-time CLI backfill above (no guessing from branch names).
- Anything that writes to GitHub other than the Project fields the sync already writes.

## Acceptance Criteria
1. Each of the three live cases is a regression fixture only (not a tuning target): coin fix shows In progress with rpg-implementer-3; STALEMATE F1 shows Parked, not Stale; #965 names rpg-implementer-2, not "seat not recorded".
2. Every new derivation reports ran / skipped / errored per item and has a positive control: an input that must produce the new value, and one that must not (a cited-only subject, a stale non-parked branch).
3. A dry run before and after is shown on one named ref and SHA, with counts of rows whose Status, Seat, Involved or Blocked-by changed, and a list of the changed rows for the owner to eyeball.
4. Report-only: the sync's exit code and `--apply` behaviour are unchanged for existing fields; a lookup that fails leaves the field empty and prints a finding.
5. Scoped tests only. The live Project write (`--init`, `--apply`) is a POST-MERGE step, not a code deliverable of this ticket (planner and owner, #715 7004743536): it runs only after a u24 seat's dry run shows the coin fix, STALEMATE F1 and #965 correctly, its moved list is shown to lead-planner and agent-working-planner, and the owner logs a yes. The prerequisites are in `docs/guidelines/session_roles/project_sync_dry_run.md`.
6. Hotspot: on a named ref, the field matches an independent count of `src/` citations across open tickets for at least 10 sampled tickets (list them), is empty for a ticket citing no `src/` file, and the top clusters match the re-measured table. Positive control: a fixture ticket citing a file cited by 3 others gets that file; must-not: a file cited only by itself.
7. The seat CLI has tests: records, refuses an unknown seat, refuses a conflicting existing record, and status.py reads it as `writing_in`.

## Related Tickets
- TCK-20261112-HAND-ADDED-WORKTREES-ARE-NOT-RECORDED-AGAINST-A-SEAT (part (a); this ticket supersedes its "parked" state)
- TCK-20261112-EPIC-GITHUB-PROJECT-TICKET-VIEW and its closed children (PROJECT-SYNC-DRY-RUN, GUARD-SEAT-AND-STALE, INIT-AND-APPLY, ALL-LANES)

## Related Docs
- `docs/guidelines/session_roles/project_sync_dry_run.md`

## Related Stored Artifacts
- none yet

## Related Code Areas
- `tools/sessions/project_sync.py` (`attribute`, `read_branch_facts`, `derive_status`, `derive_item`)
- `tools/sessions/launch.py` (`--worktree`), `tools/sessions/status.py`
- `tools/sessions/project_client.py`, `registries/session_project.yaml`

## Assumptions / Open Questions
- The four causes are lead-planner-u24's diagnosis, unverified by the planner.
- Decided (owner 7003719833): both hosts; the u24 backfill is run by a u24 seat after the merge.
- Reading #715 comments needs per-ticket matching of a free-text prefix; recall is unmeasured.
- Sequencing: behind the two dispatched mcp tickets (owner #715 7003168014); RPG first for slot and memory.

## Durable state, lifecycle and clocks
Fields added to Project 1 are a generated view of ticket files and git, rebuilt on each sync; no new durable store. Parked is derived from ticket and branch data on each run and is cleared when that data changes; no clock beyond the existing `stale_branch_days`. The Seat record in (a) is written once at worktree creation and cleared when the worktree is removed.

## Implementation Notes
Filed by agent-working-planner on lead-planner's relay of an owner request (#715 7003649308). Standard tier: needs plan, investigation and test_plan before build.

## Test Summary
301 passed before the last additions; the final scoped set is below. New: `tests/tools/test_session_project_view.py` (subject links with a positive control and must-not cases, the tests/-config-only boundary in both directions, a merged commit never counting, the merged-PR filter, Involved, Blocked by, Hotspot, hash v5, `--state-root`), `tests/tools/test_session_record_seat.py` (records the launcher's record, refuses an unknown seat, a conflicting record, a non-worktree, `--state-root` leaves the real root untouched). Existing project_sync / project_client tests were updated only for the v5 hash and the `involved=` host-facts token.

## Files Changed
`tools/sessions/project_sync.py`, `tools/sessions/project_client.py`, `tools/sessions/record_seat.py` (new), `docs/guidelines/session_roles/project_sync_dry_run.md`, `tests/tools/test_session_project_view.py` (new), `tests/tools/test_session_record_seat.py` (new), and the pinned expectations in `tests/tools/test_session_project_sync*.py` and `test_project_client.py`.

## Completion Summary
Built: (a) `record_seat.py` (reuses `state.write_bound_worktree(..., explicit=True)`; one record per seat), (b) a worktree's own commits (`--no-merges HEAD --not origin/main`) work a ticket when its id leads a subject and the commit touches a file outside `agent-working/` and `docs/`, skipped when the branch's PR is already merged, (c) Involved (recorded worktree seats; no comment parsing, 0 of 38 sampled #715 comments use the prefix), (d) Blocked by from line-start waits-on lines (Parked deferred to TCK-20261119-PROJECT-VIEW-PARKED-STATE-FROM-A-TICKET-BODY-MARKER-LINE), (e) Hotspot, hash v5, `--init` fields, `--state-root` on both CLIs.
Dry-run limits (origin/main 77e4aeb72, ubuntu, 330 items): derived Status and Seat changed on 0 rows (also on the 9 rows refreshed from origin's copy, which changed Host facts, Involved and Title/Tier/Layer/Priority/Filed only); Involved on 37 rows, Blocked by on 1, Hotspot on 95; about 314 updates and 1 create from the v4 to v5 hash bump (about 900 field writes, at least about 15 minutes at 1 s pacing). `subject-link` links 0 tickets on ubuntu because the sync reads only checked-out worktrees (the remote-branch read is TCK-20261119-PROJECT-SYNC-READS-REMOTE-BRANCHES-NOT-ONLY-CHECKED-OUT-WORKTREES); the coin fix, STALEMATE F1 and #965 are not visible from ubuntu. A seat record holds one worktree per seat, so the u24 backfill covers at most one lane per seat (remaining count unmeasured; needs the u24 worktree list). `record_seat.py` refuses non-roster seats, and the roster here has no `rpg-implementer-2` / `-3`.
Post-merge, with the owner's yes: a u24 seat's dry run shows the three owner cases and the moved list; then `--init` and `--apply` by hand (AC5). Hand-orchestrated close.
