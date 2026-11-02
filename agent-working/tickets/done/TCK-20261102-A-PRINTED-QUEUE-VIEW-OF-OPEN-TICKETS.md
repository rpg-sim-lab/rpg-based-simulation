---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261102-A-PRINTED-QUEUE-VIEW-OF-OPEN-TICKETS
phase: done
date: 2026-11-02
tags: [delivery]
---

# TCK-20261102-A-PRINTED-QUEUE-VIEW-OF-OPEN-TICKETS

## Title
A read-only command prints the open-ticket queue: order, work in flight, blocked, parked, each with its evidence or `unknown`

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner-directed through lead-planner-u24 (2026-11-02). `agent-working/tickets/todos/` holds 116 tickets on origin/main (121 on one seat's branch), mostly flat. You can't see at a glance which are in the owner's milestone order, in flight, blocked and on what, parked, or unscheduled. Priority barely separates them. The owner wants one generated view that moves no files and adds no second source of ordering; the order stays in `docs/plans/systemic_world/roadmap.md` §12.5. Reorganising `todos/` into batch folders was decided against. Owner answers and dispatch go: #715 6573753016.

Measured on origin/main, 2026-11-02 (116 tickets in `todos/`, 6 in `inprogress/`):
- **Readable today:** `## Status`, `## Priority`, `## Tier` by first token (a few carry trailing prose, such as `OPEN (counts first; ...)`), and `layer`. Status: 98 OPEN, 9 EPIC_SCOPED, 8 BLOCKED, 1 INPROGRESS. P1: 28, of which 18 are OPEN standard tickets.
- **Blocked on what:** only 1 of the 8 BLOCKED tickets names a ticket ID on its Status line. The rest would read `on: unknown`.
- **Order, not readable:** §12.5 names its steps by short name (HUNGER B, F3, N14, A', D80C). None of its 4 cited ticket IDs is an open ticket, and only 4 open tickets are cited anywhere in the roadmap. A name-to-ticket match from text would be a guess.
- **Parked, partly readable:** a rough heading-or-bold pattern hits 10 tickets; 10 more only mention the word. The pattern has at least one wrong hit: CALAMITY-INTENSITY's bold line says `ENV-06` is parked, not the ticket. The perf-pause tickets share one exact line form (`**Paused (owner, #715 ...`), which is reliable.
- **In flight:** no ticket field holds it. Open PRs and #634 claims hold it, and claims are never released.

## Scope
1. `tools/delivery/ticket_queue.py`: read-only and printed on demand, with `--json`. No file is written, so there is no new merge-conflict surface. Report-only and always exit 0 unless the tool itself fails; it is not a gate. Reuse `generate_registry.parse_body_section`/`_strip_frontmatter`, `validate_frontmatter.extract_frontmatter`, and the `ticket_field_values` enums.
2. **Source:** `origin/main` by default, read through git, with the ref and sha in the header. `--worktree` reads the working tree instead, because seat branches differ (116 against 121). `todos/` and `inprogress/` are both open states. A ticket in two status folders is flagged, not resolved.
3. **One row per ticket, with these columns:**
   - `id`, `folder`, `layer`, `priority`, `tier`, `status` (first token only).
   - `order`: from an optional `## Order Ref` body section holding a §12.5 short name (`F3`); the position always comes from the roadmap's latest order line. A name not in that line prints `stale-ref`, and no ref prints `unknown`. Optional, and not validated at close. A ticket with no order evidence is never called "unscheduled"; it reads `unknown`.
   - `blocked`: only from a BLOCKED status. `on:` lists ticket IDs from the Status line, else `on: unknown`.
   - `parked`: `yes` only on a narrow match, with `path:line` beside it so a reader can check it; `mention` when the word only appears; empty otherwise. `mention` is never counted as parked.
   - `flight`: `pr #N` from `gh pr list` (changed files or commit subjects naming the ID); `#634 comment <id>` for a #634 comment naming the ID (a mention, not necessarily a claim; narrowed from "claim" per the designer's plan review), never as running. A PR reads `pr #N closes` when its files include `done/<ID>.md`, else `pr #N touches`. If `gh` is unavailable, `unknown` with a warning. Never the word "running".
   - `epic` rows (EPIC_SCOPED or tier epic) are marked as tracking rows and left out of the work counts.
4. **Summary block:** counts per state, including `unknown` counts, plus P1 by status, tier and layer, so the size of the planned P1 triage is visible.
5. `SEQUENCE.md` membership: show the folder only. Do not read a sequence into the milestone order.
6. A short section in `docs/ai/ticket-lifecycle.md` (the path has no owning domain) naming the command and the optional `## Order Ref` section.

## Out of Scope
- Moving, renaming or foldering any ticket.
- A committed generated file, and any addition to `docs/REGISTRY.yaml`.
- A new required frontmatter or body field, and any change to the `layer` allowlist or body-field validation.
- Writing or changing the order, or editing `roadmap.md` (rpg-owned; §12.5 changes only by owner ruling).
- The P1 triage pass itself (domain planners, held until rpg's row 88 decision).
- The Agent Ops dashboard's Tickets view (TCK-20260716-AGENTOPS-TICKETS-VIEW): it filters stored fields behind a server and carries no order, parked or flight state. Not extended here.
- Fixing status text in existing tickets. The view reports it; owners fix it.

## Acceptance Criteria
1. The command prints every `TCK-*.md` under `todos/` and `inprogress/` at the named ref, exactly once per path, and the header names the ref and sha.
2. No file changes when it runs (test: tree byte-identical before and after), and a default run does not read the working tree's tickets.
3. Every state column is either backed by evidence shown in the row or reads `unknown`/`mention`. Fixtures cover: `OPEN (prose ...)`, `BLOCKED` with and without an ID, `previously BLOCKED` prose in an OPEN status (reads OPEN), the bold `ENV-06 ... parked` line (not `yes`), the `**Paused (owner, ...` line (`yes`), and `Parked time:` (`mention`).
4. With `gh` unavailable, the view still prints, `flight` reads `unknown`, and a warning says so.
5. The summary prints `unknown` counts and P1 counts by status, tier and layer. `--json` carries the same data.
6. A run against the real tree is recorded in `investigation.md`, with every `parked: yes` row checked by hand and the false-positive count stated.
7. Order per the owner's answer (`## Order Ref`, #715 6573753016), with a test against the real §12.5 line, and fixtures for an in-line ref, a `stale-ref` and no ref. Position is never stored on a ticket: if the line can't be parsed, every row reads `unknown` and a warning says so. It never falls back to a text-match guess.

## Related Tickets
- TCK-20261101-PR-RENDER-LEAVES-OUT-A-TICKET-IN-TWO-STATUS-FOLDERS (two-folder trouble)
- TCK-20260929-OPEN-TICKET-DUPLICATE-SCAN-AND-WORKFLOW-OFFER (`open_ticket_overlap.py`: overlap, not state)
- TCK-20260718-TICKET-CORPUS-REPORT (`ticket_stats_report.py`: `done/` only, not open work)
- TCK-20260716-AGENTOPS-TICKETS-VIEW (dashboard table)

## Related Docs
- `docs/plans/systemic_world/roadmap.md` §12.5 (the owner's order; change control there)
- `docs/ai/ticket-lifecycle.md`

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261102-A-PRINTED-QUEUE-VIEW-OF-OPEN-TICKETS/ (plan.md, investigation.md, test_plan.md)

## Related Code Areas
- `tools/delivery/ticket_queue.py` (new; agent-working)
- `tests/tools/test_ticket_queue.py` (new)
- `tools/ticket_field_values.py`, `tools/generate_registry.py`, `tools/validate_frontmatter.py` (read-only reuse)

## Assumptions / Open Questions
1. **Answered by the owner (#715 6573753016):** an optional `## Order Ref` body section holds the §12.5 short name; the position always comes from the roadmap, so there is no second order. rpg-planner fills the tickets behind the named steps as separate work (not in this ticket). Dispatched as standard tier with the designer reviewing plan.md, same comment.
2. **Per-domain P1 counts:** `layer` doesn't map to a seat domain, and routing a ticket's Related Code Areas would be a guess. v1 prints by layer. Open to a mapping if the triage pass needs one.
3. Parsing §12.5's prose order line is fragile (it has been amended by appended sentences). AC7 makes failure visible rather than silent; if it fails often, that is evidence for having §12.5 cite ticket IDs, an owner ruling.

## Implementation Notes
Designer amendments A-D folded in (section 12.5 scope and path:line in the header, gh limits and caps, closes/touches labels, verbatim-fixture order test). A fourth `parked: yes` pattern (`**Parked**`) was added after the AC6 hand check. `gh pr list` asks for `number,title,files` only: adding `commits` exceeds gh's GraphQL node cap. The default `--limit` is 300, with a warning when reached.

## Test Summary
`pytest tests/tools/test_ticket_queue.py tests/tools/test_delivery_pr_render.py -q -p no:randomly`: all pass (17 new tests). AC6 real-tree run, with every `parked: yes` row checked by hand (0 false positives of 8), is in investigation.md.

## Files Changed
tools/delivery/ticket_queue.py (new); tests/tools/test_ticket_queue.py (new); docs/ai/ticket-lifecycle.md.

## Completion Summary
`ticket_queue.py` prints the open-ticket queue read-only, each state backed by shown evidence or `unknown`/`mention`. Not done here, by scope: filling `## Order Ref` on tickets (rpg-planner), editing roadmap.md, the P1 triage. Known gap: 3 real parks read `mention` because the patterns are narrow by design.
