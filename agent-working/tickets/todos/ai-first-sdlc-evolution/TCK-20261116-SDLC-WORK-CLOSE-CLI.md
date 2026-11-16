---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-SDLC-WORK-CLOSE-CLI
phase: open
date: 2026-11-16
tags: [ai, delivery]
---

# TCK-20261116-SDLC-WORK-CLOSE-CLI

## Title
A `work close` command closes a ticket in one step and refuses when a validator fails.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
SDLC Phase 2, filed by agent-working-planner on 2026-11-16 under the owner's OD decisions (#715 6910853925). Filing only: dispatch needs a separate owner go. Plan §39 Phase 2 item 3: "Add a `work close` CLI: atomic transition (move, frontmatter, body status, artifacts, log row, registry), idempotent, refuses on failed validators."

Today a close takes several steps from CLAUDE.md "After Work":
- move the ticket;
- fix the frontmatter;
- migrate the staging artifacts;
- `record_hand_orchestrated_closure.py`;
- `done_checker_static.py`;
- the mechanism advisory;
- the registry.

Known failure modes are written down in the repo:
- a double working-log row (TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE);
- a todos/ duplicate left behind;
- a missed registry regeneration.

## Scope
1. One command, for example `python3 -m tools.delivery.work_close --ticket-id <ID> --tier <t> --path-reason <r> [--path-note ...] --events <json>`. It does the following, in order:
   - moves the ticket to `done/`, and removes the `todos/` source, handling the epic-folder rule;
   - sets `status: historical` and `phase: done`, and `## Status DONE`;
   - migrates the staging artifacts for standard and epic tiers;
   - records the run, the events and the working-log row through the existing closure tool, without writing a second row;
   - regenerates `docs/REGISTRY.yaml`;
   - runs `done_checker_static --ticket-id` and the mechanism advisory. The advisory stays report-only.
2. **Refusal.** If a validator fails, the command stops before any move, writes nothing, and names the failed condition. It never edits an artifact to pass a check.
3. **Idempotent.** A second run on a closed ticket reports "already closed" and changes nothing.
4. **Reuse.** It calls `record_hand_orchestrated_closure.py`, `working_log_writer.append_working_log_row()` (indirectly), `done_checker_static` and `generate_registry`. It reimplements none of them.
5. **Docs.** `docs/guides/delivery_process.md` gets a section on the command. The CLAUDE.md "After Work" text becomes a pointer to it (plan §39 Phase 2 item 4). CLAUDE.md is a governing file: the exact diff goes to the owner, who approves it directly, and it is not committed before that.

## Out of Scope
- The CI gate job: TCK-20261116-SDLC-CLOSE-CHECK-REPORT-ONLY-GATE-JOB.
- The closure record format (L1): TCK-20261116-SDLC-CLOSURE-RECORD-AND-EVIDENCE-LAYERS. Once that lands, the command writes the record through the same entry point.
- Pushing, opening a PR, or merging.
- Changing `implement-ticket.js`'s Finalize (OD-5 is open).

## Acceptance Criteria
1. In a temp tree, a standard ticket goes from `inprogress/` to `done/` in one call. `done_checker_static` then passes, there is exactly one log row, and the registry is in sync.
2. With a failing validator, nothing moves and the exit code is non-zero with the condition named. Shown by a test.
3. A second call is a no-op, shown by a test.
4. An epic-folder child: the last child's close moves the folder to `done/`, and an earlier child's close does not. Shown by a test.
5. The CLAUDE.md pointer change is either applied with the owner's direct OK or listed as pending.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20260914-DONE-CHECKER-UNREACHABLE-FROM-HAND-ORCHESTRATED-CLOSURE
- TCK-20260912-WORKING-LOG-APPEND-HELPER
- TCK-20261116-SDLC-CLOSE-CHECK-REPORT-ONLY-GATE-JOB

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (§39 Phase 2)
- docs/guides/delivery_process.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/agent-monitoring/record_hand_orchestrated_closure.py
- tools/working_log_writer.py
- tools/gate_checks/done_checker_static.py
- tools/mechanism_registry/mechanism_registry_changed_code_check.py

## Assumptions / Open Questions
- The command lives in `tools/delivery/`, which agent-working owns. Check with `route` before creating the file.
- "Atomic" means it stops before the first write on any validator failure. A crash part-way through is reported with the steps already done, so it can be rerun. A true filesystem transaction is not attempted.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
