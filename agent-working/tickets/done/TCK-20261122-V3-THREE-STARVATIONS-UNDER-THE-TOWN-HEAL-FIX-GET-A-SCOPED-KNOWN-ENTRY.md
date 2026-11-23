---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261122-V3-THREE-STARVATIONS-UNDER-THE-TOWN-HEAL-FIX-GET-A-SCOPED-KNOWN-ENTRY
phase: done
date: 2026-11-22
tags: [testing]
---

# TCK-20261122-V3-THREE-STARVATIONS-UNDER-THE-TOWN-HEAL-FIX-GET-A-SCOPED-KNOWN-ENTRY

## Title
Gate V3 on three bodies that starve once #991's town-heal fix lands gets a scoped known entry that expires on 2026-12-15

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Gate run 44998631861 on #991 (4e6a06fa5, behaviour-identical to da8a660ec) against main run 44998634291 (613a8365b) shows three unowned V3 rows: frontier_living_world/45 human 5 t3472, crowded_frontier/45 goblin 30 t3618, frontier_living_world/42 goblin 30 t2588. The designer rules them exposed pre-existing defects, not a #991 regression. The cause is unread: the gate documents record no project, objective or wage (/data/vboxuser/testing-planner-notes/town_heal_991_v3_rows_read.md). Draft entry: town_heal_991_known_entry_draft.md, same folder. Merge order (lead-planner, rpg-planner): this PR (step A) first, then #991, then the e55 removal (step C) in the next testing PR.

## Scope
Append one scoped V3 `state: fail` entry to tools/test_architecture/rpg_gate_known.yaml with three cases (world, seed, entity), ticket TCK-20261122-THREE-STARVING-BODIES-DIE-WITH-WAYS-UNTRIED-ONCE-THE-TOWN-HEAL-STOPS-HIDING-THEM, owner rpg-planner, added_on 2026-11-22, expires_on 2026-12-15. Carry that cause ticket as an exact blob copy (a0639eed9) so the entry's live-ticket lint passes. The e55 entry is kept.

## Out of Scope
- The cause or fix of the three deaths (the cause ticket).
- The e55 entry removal (step C, with the next testing PR).
- Any other gate row, the V3 check, thresholds, baselines or config.

## Acceptance Criteria
1. The entry is in the known file as the draft, scoped to three (world, seed, entity) cases, and the e55 entry is unchanged.
2. known_reds lint reports no problems and the gate tool tests pass.
3. The owner's yes on the entry is recorded on #715 before merge.

## Related Tickets
- TCK-20261122-THREE-STARVING-BODIES-DIE-WITH-WAYS-UNTRIED-ONCE-THE-TOWN-HEAL-STOPS-HIDING-THEM (owner of the rows)
- TCK-20261121-V3-FLW-S42-E55-GETS-AN-OWNER-ACCEPTED-SCOPED-KNOWN-ENTRY (#989 precedent; its entry is kept until step C)
- TCK-20261107-THREE-CROWDED-V3-STARVATIONS-GET-SCOPED-KNOWN-ENTRIES (#839 precedent)

## Related Docs
- tools/test_architecture/known_reds.py (schema and lint, the module docstring)

## Related Stored Artifacts
None.

## Related Code Areas
- tools/test_architecture/rpg_gate_known.yaml

## Assumptions / Open Questions
- The matcher checks (world, seed, entity_id) and that all violations show in the examples; it does not check tick, kind or the untried list, which live in the note.
- "Earlier of the fix landing" is enforced by the cause ticket's closer removing the entry (the lint fails once that ticket is in done/).

## Durable state, lifecycle and clocks
The entry expires on 2026-12-15. By then the cause ticket retires it (the rows are gone, with evidence) or renews it once, with evidence and a new date.

## Implementation Notes
Entry appended after the e55 entry. Its cases differ from the e55 case, so nothing is shadowed or overlapping.

## Test Summary
Executed on testing-planner-v3-known-entry (origin/main 613a8365b), taskset 0-3:
- tests/unit/tools/test_known_reds.py: 57 passed.
- tests/unit/tools -k "known or rpg_gate_report or rpg_gate_baseline": 268 passed.

## Files Changed
- tools/test_architecture/rpg_gate_known.yaml
- agent-working/tickets/todos/TCK-20261122-THREE-STARVING-BODIES-DIE-WITH-WAYS-UNTRIED-ONCE-THE-TOWN-HEAL-STOPS-HIDING-THEM.md (blob copy)

## Completion Summary
The scoped V3 entry for the three #991 starvations is in the known file, pending the owner's yes. The cause ticket stays open.
