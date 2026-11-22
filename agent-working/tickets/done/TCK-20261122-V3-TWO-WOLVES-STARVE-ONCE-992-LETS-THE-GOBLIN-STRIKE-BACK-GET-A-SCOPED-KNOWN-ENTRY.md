---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261122-V3-TWO-WOLVES-STARVE-ONCE-992-LETS-THE-GOBLIN-STRIKE-BACK-GET-A-SCOPED-KNOWN-ENTRY
phase: done
date: 2026-11-22
tags: [testing]
---

# TCK-20261122-V3-TWO-WOLVES-STARVE-ONCE-992-LETS-THE-GOBLIN-STRIKE-BACK-GET-A-SCOPED-KNOWN-ENTRY

## Title
Gate V3 on two wolves that starve once #992 lands gets a scoped known entry that expires on 2026-12-15

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
The gate read of #992 (dffe0a6e1, run 45018320010) against main (67c65321, run 45018323188) shows two unowned V3 rows: frontier_living_world/42 wolf 47 t3553 and frontier_living_world/45 wolf 49 t3969, both untried HUNT_EAT_RAW and SCAVENGE (/data/vboxuser/testing-planner-notes/strike_permission_992_moved_rows_v2.md, wolf_992_known_entry_draft.md). rpg-designer ruled them exposed and pre-existing, not a #992 regression (#715 7081250432). Merge order: this PR first, then #992, then the shrink of the #994 entry in the next testing PR.

## Scope
Append one scoped V3 `state: fail` entry to tools/test_architecture/rpg_gate_known.yaml with two cases, ticket TCK-20261122-A-STARVING-PREDATOR-HAS-NO-FALLBACK-WAY-TO-EAT, owner rpg-planner, added_on 2026-11-22, expires_on 2026-12-15. Carry that cause ticket as an exact blob copy (ad62f98a5) so the entry's live-ticket lint passes.

## Out of Scope
- The cause or fix of the starvations (the cause ticket).
- Shrinking the #994 entry and removing the e55 entry (next testing PR, after #992 is on main).
- Any other gate row, threshold, baseline or config.

## Acceptance Criteria
1. The entry is in the known file as the draft; the #994 and e55 entries are unchanged.
2. known_reds lint reports no problems and the gate tool tests pass.
3. The owner's yes on the push is recorded on #715 before the push.

## Related Tickets
- TCK-20261122-A-STARVING-PREDATOR-HAS-NO-FALLBACK-WAY-TO-EAT (owner of the rows)
- TCK-20261122-V3-THREE-STARVATIONS-UNDER-THE-TOWN-HEAL-FIX-GET-A-SCOPED-KNOWN-ENTRY (#994 precedent)

## Related Docs
- tools/test_architecture/known_reds.py (schema and lint)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/test_architecture/rpg_gate_known.yaml

## Assumptions / Open Questions
- A scoped case that matches no failing row owns nothing and is harmless, so the entry may merge before #992.

## Durable state, lifecycle and clocks
The entry expires on 2026-12-15; the cause ticket's closer removes it earlier.

## Implementation Notes
Appended after the #994 entry; its cases differ from every other case.

## Test Summary
See the PR review notes.

## Files Changed
tools/test_architecture/rpg_gate_known.yaml; the cause ticket copy; this ticket.

## Completion Summary
Entry added; no gate expectation changes until #992 lands.
