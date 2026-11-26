---
status: active
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261125-A-COHORT-IN-FRONTIER-NEVER-SLEEPS-FOR-ABOUT-2000-TICKS
phase: open
date: 2026-11-25
tags: [cognition]
---

# TCK-20261125-A-COHORT-IN-FRONTIER-NEVER-SLEEPS-FOR-ABOUT-2000-TICKS

## Title
A cohort in frontier_living_world never sleeps for about 2,000 ticks, and what refused bodies do after the K2 fix's WAY_CLOSED is unread.

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P2

## Request Summary
Filed by rpg-planner on 2026-11-25 as a BACKLOG item for the cognition-rework backlog. It is NOT HARD under roadmap §12.5 (rpg-designer's classification). Owner ruling #715 7165253893: "Merge K2 on this evidence". The K2 fix PR carries this as its BALANCE line and names this ticket.

Evidence (rpg-designer, drafts/rpg-designer-k2fix-frontier-view.md, sha256 002091941ae74730…; executed from main's intact own-job v3 spy JSON, /mnt/data2/rpg-measure/k2fix_ownjob_v3_out/main/):
- On main d084b9248, frontier_living_world s42, 5,000 t: 25 subjects reach sleep_debt ≥ 98. Of those, 21 reach it at the SAME tick, t1961 (0.05 × 1961 from 0).
  - They never slept, were never lodged, and had gold 0.
  - They held stabilize, town_return or combat_engage projects.
- With the K2 fix (282b25981), the same measure is 30 (run 1, k2fix_ownjob_out). The most likely reading is that the same never-slept cohort is larger on a diverged trajectory. That's an inference: the fix arm's windows were lost to the v3 kit's serialization crash.
- Also unread: what subjects refused by the K2 fix's (A) WAY_CLOSED (an unpayable inn bed) do in the next 200 t. That's own-job A(ii), which never produced fix-arm data.

## Scope
- Find why a cohort that keeps_coin has gold 0 and never chooses sleep for about 2,000 t: which project holds them, and whether fatigue ever wins scoring for them.
- Read the K2 fix's WAY_CLOSED follow-ups (A(ii)) with a serialization-fixed own-job kit, if still needed after the cognition rework.

## Out of Scope
- Changing the K2 fix.
- Any HARD repair. A finding that turns out HARD (a state that never exits) goes to rpg-planner for an owner ruling.

## Acceptance Criteria
- A cause statement for the never-slept cohort on main, with typed evidence.
- A rpg-designer ruling on whether it is a liveness defect or design behaviour.

## Related Tickets
- TCK-20261029-A-SERVICE-DISPATCH-THAT-FAILS-EVERY-TICK-NEVER-BECOMES-A-BLOCKER (the K2 fix; its BALANCE line names this ticket)
- TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH (K3, SURV-07)
- overlap scan: not run yet; run it at dispatch.

## Related Docs
- docs/plans/systemic_world/roadmap.md §12.5 (BALANCE class)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/k2fix_ownjob_v3_out/main/ (main's v3 spy JSON, b9b8c985…)

## Related Code Areas
- src/ai/goals/scorers.py (SleepScorer), src/systems/strategic_systems/intelligence.py

## Assumptions / Open Questions
- Is a 2,000 t never-slept stretch a state that never exits (HARD) or one that would exit later? Not read past 5,000 t.

## Durable state, lifecycle and clocks
- None new.

## Implementation Notes
- Not started.

## Test Summary
- None.

## Files Changed
- None.

## Completion Summary
- Open.
