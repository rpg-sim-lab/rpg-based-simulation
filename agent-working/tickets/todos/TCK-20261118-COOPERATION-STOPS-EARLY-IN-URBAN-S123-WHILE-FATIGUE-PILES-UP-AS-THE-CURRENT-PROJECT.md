---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261118-COOPERATION-STOPS-EARLY-IN-URBAN-S123-WHILE-FATIGUE-PILES-UP-AS-THE-CURRENT-PROJECT
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-COOPERATION-STOPS-EARLY-IN-URBAN-S123-WHILE-FATIGUE-PILES-UP-AS-THE-CURRENT-PROJECT

## Title
In urban_political s123 the last cooperation_event is around t1460-1630 of 5000, and late in every urban run 9-15 subjects hold 'fatigue' as their current project; pre-existing on main, cause unread

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Found by the churn fix's own-job (capread_n10.py 59b0813b over each cell's run dir; 2026-11-18). rpg-designer ruled it ONE separate, pre-existing liveness finding (the s123 stop and the fatigue pile-up together). It does not gate the churn merge, but it IS a HARD liveness item at the run-1 boundary read: resolved, or accepted by the owner, before that read (rpg-designer packet drafts/rpg-designer-churn-ownjob-ruling.md, sha 729bc878).
- Last cooperation_event tick, main dca5a8dbb -> churn fix 18c3250a4: urban s42 4900 -> 4900; urban s123 1460 -> 1630; frontier s42 4900 (fix); crowded s42 4862 (fix).
- Current project kind at t4900: 'fatigue' for 9-15 subjects in urban, on BOTH arms. Main also keeps one resolve_blocker.
- The 5000-tick metric does not separate main from fix in s42, so the churn ticket's "cooperation resumes" claim is restated (owner ask, rpg-designer), and the early stop in s123 is tracked here.

## Scope
1. Cause read first, no behaviour change. Is fatigue the current project because nothing ends it (a project with no completion or abandonment path at night or under low stamina)? Why does cooperation stop in s123 near t1500 on both arms? Use the existing run dirs: blockerchurn/tree_{fix,main}/data/runs/... (cells_main and cells_fix spy JSON "run_dir").
2. rpg-designer rules the class before code.
3. Fix, tests, own-job. Bars are fixed before data.

## Out of Scope
- The resolve_blocker churn (its own ticket).

## Acceptance Criteria
- The cause is named with evidence.
- After a fix: no subject holds fatigue as its current project beyond a ruled bound, and cooperation continues in urban s123 to the run's end, or the ruled reason it shouldn't is documented.

## Related Tickets
- TCK-20261117-A-RESOLVE-BLOCKER-PROJECT-IS-RE-CREATED-EVERY-80-TICKS-AND-STALLS-COOPERATION (its own-job found this)
- TCK-20261118-A-SUBJECT-WITH-A-STANDING-HELP-NEED-RE-DECIDES-SOLO-EVERY-TICK (cooperation path)

## Related Docs
- docs/mechanics/04_strategic_cognition.md; docs/mechanics/01_entity_anatomy.md (fatigue/sleep pressure)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/blockerchurn/cells_{fix,main}/*_capread.txt

## Related Code Areas
- the strategic project lifecycle for 'fatigue' projects; the cooperation phase

## Assumptions / Open Questions
- Whether fatigue's pile-up and the cooperation stop share a cause is unknown.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
