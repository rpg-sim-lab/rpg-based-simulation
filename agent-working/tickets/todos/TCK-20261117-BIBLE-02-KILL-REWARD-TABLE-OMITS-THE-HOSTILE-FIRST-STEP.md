---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261117-BIBLE-02-KILL-REWARD-TABLE-OMITS-THE-HOSTILE-FIRST-STEP
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-BIBLE-02-KILL-REWARD-TABLE-OMITS-THE-HOSTILE-FIRST-STEP

## Title
Bible 02's kill-reward table omits the hostile-first step

## Status
OPEN

## Tier
standard

## Type
repair

## Priority
P1

## Request Summary
Deeper issue 1 (HARD: Bible/parity truth). combat_rewards.py:71-106 gives a hostile pair 10 xp / 5 gold whatever the role; docs/mechanics/02_combat_laws.md's kill-reward table does not state this hostile-first step. The doc and the code disagree, which breaks the parity law.

Source: rpg-designer M1 items 2-6 rule text (main-checkout .claude/handover/drafts/rpg-designer-m1-items-2-6-rule-text.md, sha256 800027b5), section 'Deeper issues'. Filed by rpg-planner under owner ruling #715 6936893143 (deeper issues found in Phase 1 are filed now and fixed in Phase 3 unless they are hard errors).

## Scope
1. Read combat_rewards.py:71-106 and the Bible 02 table; state the exact gap.
2. Mark the parity ledger row (progression.yaml / combat_movement.yaml reward rows) divergent now, via tools/parity_ledger_writer.py --check.
3. Correct the Bible 02 table to the code as it is today (doc truth, no behaviour change). The reward rule itself may change later under owner Q8 (rewards keyed to the power band).

## Out of Scope
- Changing reward amounts (owner Q8, M1 Item 2).

## Acceptance Criteria
- Bible 02's table states the hostile-first step exactly as the code applies it.
- The ledger row is verified against a test that pins the hostile-first case.
- No src behaviour change.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Related Docs
- docs/mechanics/ (the chapter for this subsystem)

## Related Stored Artifacts
- none yet

## Related Code Areas
- as named in the Request Summary

## Assumptions / Open Questions
- The line numbers are on main bb26e4e5f, from the designer's reading; re-check them before acting.

## Implementation Notes
- Phase 1 (HARD: doc truth). rpg-planner assigns it to the first free lane.
- Binding M1 rule: new species reads use species_of(), label reads use occupation_of(); never read `kind`.

## Test Summary

## Files Changed

## Completion Summary
