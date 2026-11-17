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
SEQUENCED PAIR with Q8 (owner #715 6937049127: Q8 (a) keys XP and gold to the defeated body's power band and level; lead: don't correct the Bible twice):
1. NOW (Phase 1, this ticket): mark the parity ledger reward row(s) divergent via tools/parity_ledger_writer.py --check, with a divergence_note naming the hostile-first step (combat_rewards.py:71-106) and this ticket. Bible 02 is NOT edited here.
2. THEN (in M1 Item 2, TCK-20261109-M1-COARSE-PROPERTY-BANDS-AND-THE-APPRAISAL, run 3): the Q8 change rewrites the reward path, and Bible 02's table is rewritten once to the new band/level rule. The ledger row returns to verified with a test that pins it. Item 2's ticket carries this as an AC.

## Out of Scope
- Changing reward amounts, and the Bible 02 table rewrite: both are in Item 2 (Q8).

## Acceptance Criteria
- The reward ledger row(s) read divergent with a note citing this ticket and Item 2. No Bible or src edit in this ticket.
- Item 2's ticket names the Bible 02 rewrite and the return to verified as its own AC.

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
- Phase 1 (HARD: doc truth): the ledger marking is small and goes to the first free lane; the Bible rewrite rides Q8 in Item 2.
- Binding M1 rule: new species reads use species_of(), label reads use occupation_of(); never read `kind`.

## Test Summary

## Files Changed

## Completion Summary
