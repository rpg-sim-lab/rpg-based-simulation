---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261114-NAVIGATION-CLEAR-TARGET-FLAG-IS-NEVER-APPLIED
phase: open
date: 2026-11-14
tags: [engine]
---

# TCK-20261114-NAVIGATION-CLEAR-TARGET-FLAG-IS-NEVER-APPLIED

## Title
NavigationUpdate.clear_target is never applied, so three writers that mean to drop a stored target drop nothing

## Status
OPEN

## Tier
standard

## Type
bug

## Priority
P3

## Request Summary
Found by lane A while drafting the HOLD plan (TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP, 2026-11-14), verified by rpg-planner on origin/main. NavigationUpdate carries two clear flags: target_clear (applied, src/core/patches.py:284) and clear_target (src/core/updates.py). clear_target is only merged (updates.py:208) and read (src/engine/pipeline_phases/actor_validity.py:76); no patch applies it to state. Its writers therefore clear no stored target: src/engine/movement.py:413 (`clear_target=replan`, the oscillation / wait_count>=5 replan), src/engine/pipeline_phases/actor_validity.py:116, src/engine/blacksmith.py:250.

Designer (rpg-designer, 2026-11-14, session message): separate ticket, P3 pending a sizing read; raise to P2 if the replan case feeds the reroute F,F,S loops.

## Scope
1. Read-only sizing first: how often the movement.py:413 replan fires with clear_target=True while the stored target survives, and what happens next (does the subject re-walk the same target, re-enter the congestion ladder, feed rung-3.3 reroutes?). Same for actor_validity.py:116 and blacksmith.py:250.
2. Designer rules meaning and fix shape after sizing (e.g. apply the flag, or fold writers onto target_clear and remove the dead flag).

## Out of Scope
- The HOLD fix (it uses target_clear and pins both flags as they are).
- The reroute legality bypass itself.

## Acceptance Criteria
- Sizing delivered; priority confirmed or raised; designer ruling recorded; then fix (with tests for each writer) or close per ruling.

## Related Tickets
- TCK-20261111-A-HOLD-MODE-MOVE-STILL-TAKES-A-STEP (found by)
- TCK-20261114-REROUTE-RUNG-STEPS-PAST-THE-READINESS-GATE-AND-STATUS-BLOCK (possible feed into F,F,S loops)

## Related Docs
- docs/engine/authoritative_mutation_pipeline_contract.md

## Related Stored Artifacts
- /mnt/data2/rpg-measure/briefs/hold-cells-report.md (off-repo)

## Related Code Areas
- src/core/updates.py (NavigationUpdate.clear_target, merge :208), src/core/patches.py:284
- src/engine/movement.py:413, src/engine/pipeline_phases/actor_validity.py:76/:116, src/engine/blacksmith.py:250

## Assumptions / Open Questions
- Was clear_target intended as an alias of target_clear?

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
