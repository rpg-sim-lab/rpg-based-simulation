---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261109-M1-PLACES-ARE-FOUND-FROM-PERCEPTION-AND-MEMORY
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-M1-PLACES-ARE-FOUND-FROM-PERCEPTION-AND-MEMORY

## Title
Food and other places are found from what the subject perceives, remembers or was told, not from the true map (decision 56)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Roadmap §12.3 milestone 1, decision 56.

Child of TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC.

Filed by rpg-planner on 2026-11-09 as a filing only (no code), on lead-planner-u24's go relaying the owner (#715 6731822583). This follows roadmap §12.5: "Each item becomes a ticket under the milestone 1 epic before work starts."

## Scope
1. List every decision that reads the true map to find a place.
2. Move each one to perceived, remembered or told knowledge, under the uncertainty rule (vague leads stay vague).
- Rule work before code (§12.3, "How the path runs"): the catalog text and kernel spec come first. Owner-level choices go to the owner as questions with options and a recommendation when the milestone starts. The forward design's proposed recommendations are not rulings.
- Measured as its own step, once at fold against its parent (decision 76), on the cumulative watch that restarts at v1.1, with the §12.5 per-step stop rules. Those rules and the watch are not trimmed without an owner ruling (#715 6731822583). The measurement tier is stated at dispatch under the standing depth rule (#715 6731764470). It is never below the floor (#715 6731822583): the paired default tier plus every world where an affected known entry lives. A hash-equal check alone proves only an observability change. Decision 76 (§12.3) sets a behaviour step at 3 worlds x 5 seeds x 5000 ticks per arm, and going below it needs an owner ruling.

## Out of Scope
- §12.4 (packs, herds, territory), milestones 2 and 3, and any rule work not listed in §12.3 (owner ruling only).

## Acceptance Criteria
- PERF BUDGET (owner #715 6968328816): a before/after profile of the replaced read vs nearest_town_tile, within a budget set from perf-planner's quiet-host baseline (no number until that baseline exists). A regression is fixed or explicitly accepted by the owner, never deferred (M1 epic regression rule).
- No place-finding decision reads the true map.
- A subject that knows no food place does not walk to one.
- Tests for the new behaviour, plus the parity ledger and Bible updates in the same change.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC

## Related Docs
- docs/plans/systemic_world/m1_kernel_spec_items_2_6.md (the kernel spec + this item's own-job counts; owner answers Q1-Q10, #715 6937049127)
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5 done criteria)
- docs/plans/systemic_world/owner_decision_memo.md

## Related Stored Artifacts
None.

## Related Code Areas
src/strategy/, knowledge and memory

## Assumptions / Open Questions
- Order (roadmap §12.5, memo rows 89/93/95): the v1-disclosure repairs, then D80C, then the decision-73 step (#781, the v1.1 record), then the §12.3 items. Starting this item needs the owner's dispatch yes, brought by rpg-planner via lead-planner-u24.
- Owner-level choices are asked when the milestone starts, not guessed here.

- COST BAR (rpg-planner, 2026-11-18, from perf-planner's engine profile on main 99a83adc9, docs/performance/tick_cost_growth.md §10 at perf-planner-next 09e2faa38). Today's true-map read `nearest_town_tile` (intelligence.py:397/:674, redirection.py:138; a min() with a lambda over every town tile, per entity) is 39-62% of fused_strategic_pass, which is 21-28% of the tick. This item retires that read, so it is NOT optimised separately. The replacement read (perception and memory) must not cost more than that share; measure it in this item's own-job. It touches intelligence.py, so it lands after or inside TCK-20261117-SPLIT-INTELLIGENCE-PY-BELOW-ITS-LINE-CEILINGS.

## Implementation Notes
- 2026-11-19 FOLDED IN (rpg-designer's follow-up from #781 SEEK_WORK; folded here rather than filed separately, because this item already moves place-finding to known places). The designer's wording:
  "A subject knows where hiring places and shops are: a typed place-knowledge fact (building id, kind, position, learned_tick, source), learned by sight or by being told, and decaying like other facts. SEEK_WORK then targets the nearest KNOWN hiring or shop building outside reach, else town_center. The existing in-leash steps (forage, work_in_reach, shop_sale) keep reading the true map inside the leash, out of scope here. Acceptance: SEEK_WORK picks a known building over town_center when it has one; with no fact it targets town_center as today; place facts are typed records on the knowledge component and visible in inspection."
  - Context: #781 (TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1) ships SEEK_WORK targeting state.town_center. No building-knowledge fact type exists in code: KnowledgeModelComponent's fact types are resource_source, recipe_definition, danger_rating, lead and behavior_report (inspected by lane A, 2026-11-19).
  - Rule text: drafts/rpg-designer-m1-items-2-6-rule-text.md (M1 run 2, see and find).
None yet.

- 2026-11-17 (rpg-planner, from the designer's rule text 800027b5, deeper issue 6): GuildAction.visit writes VAGUE leads with true-map exact coordinates. This item fixes it (a lead keeps only what the teller knew); add a test that a guild-visit lead carries no exact true-map coordinates.

## Test Summary

## Files Changed

## Completion Summary
