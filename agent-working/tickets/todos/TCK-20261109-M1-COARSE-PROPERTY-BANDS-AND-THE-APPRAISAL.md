---
status: active
layer: simulation
authority: P1
audience: agent
ticket_id: TCK-20261109-M1-COARSE-PROPERTY-BANDS-AND-THE-APPRAISAL
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-M1-COARSE-PROPERTY-BANDS-AND-THE-APPRAISAL

## Title
Kinds carry a property model in coarse bands, as schema and content, and subjects appraise each other by it

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Roadmap §12.3 milestone 1: "The property model in coarse bands, as schema and content" and "The appraisal."

Child of TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC.

Filed by rpg-planner on 2026-11-09 as a filing only (no code), on lead-planner-u24's go relaying the owner (#715 6731822583). This follows roadmap §12.5: "Each item becomes a ticket under the milestone 1 epic before work starts."

## Scope
1. Write the band schema (rule work first), then the content for every kind.
2. Build the appraisal that reads the bands in place of names.
- Rule work before code (§12.3, "How the path runs"): the catalog text and kernel spec come first. Owner-level choices go to the owner as questions with options and a recommendation when the milestone starts. The forward design's proposed recommendations are not rulings.
- Measured as its own step, once at fold against its parent (decision 76), on the cumulative watch that restarts at v1.1, with the §12.5 per-step stop rules. Those rules and the watch are not trimmed without an owner ruling (#715 6731822583). The measurement tier is stated at dispatch under the standing depth rule (#715 6731764470). It is never below the floor (#715 6731822583): the paired default tier plus every world where an affected known entry lives. A hash-equal check alone proves only an observability change. Decision 76 (§12.3) sets a behaviour step at 3 worlds x 5 seeds x 5000 ticks per arm, and going below it needs an owner ruling.

## Out of Scope
- §12.4 (packs, herds, territory), milestones 2 and 3, and any rule work not listed in §12.3 (owner ruling only).

## Acceptance Criteria
- Every placed kind declares its bands in content.
- The appraisal reads only bands and perceived state, never a name.
- Tests for the new behaviour, plus the parity ledger and Bible updates in the same change.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Related Docs
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5 done criteria)
- docs/plans/systemic_world/owner_decision_memo.md

## Related Stored Artifacts
None.

## Related Code Areas
content schemas, src/strategy/ (appraisal)

## Assumptions / Open Questions
- Order (roadmap §12.5, memo rows 89/93/95): the v1-disclosure repairs, then D80C, then the decision-73 step (#781, the v1.1 record), then the §12.3 items. Starting this item needs the owner's dispatch yes, brought by rpg-planner via lead-planner-u24.
- Owner-level choices are asked when the milestone starts, not guessed here.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
