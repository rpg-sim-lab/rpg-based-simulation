---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES
phase: open
date: 2026-11-09
tags: []
---

# TCK-20261109-M1-RETIRE-ROLE-KIND-AND-FACTION-NAME-BRANCHES-IN-STAGES

## Title
Retire behaviour that branches on role, kind or faction names, in stages, measured each time, including the camp tether (decision 57)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Roadmap §12.3 milestone 1: "Retire behaviour that branches on role, kind or faction names, in stages, measured each time. This includes the fixed camp tether, replaced by a home range (decision 57)."

Child of TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC.

Filed by rpg-planner on 2026-11-09 as a filing only (no code), on lead-planner-u24's go relaying the owner (#715 6731822583). This follows roadmap §12.5: "Each item becomes a ticket under the milestone 1 epic before work starts."

## Scope
1. Inventory every name branch in decision paths (the probe ticket gives the list).
2. Retire them in stages, and measure each stage as its own step.
3. Replace the fixed camp tether with a home range.
- Rule work before code (§12.3, "How the path runs"): the catalog text and kernel spec come first. Owner-level choices go to the owner as questions with options and a recommendation when the milestone starts. The forward design's proposed recommendations are not rulings.
- Measured as its own step, once at fold against its parent (decision 76), on the cumulative watch that restarts at v1.1, with the §12.5 per-step stop rules. Those rules and the watch are not trimmed without an owner ruling (#715 6731822583). The measurement tier is stated at dispatch under the standing depth rule (#715 6731764470). It is never below the floor (#715 6731822583): the paired default tier plus every world where an affected known entry lives. A hash-equal check alone proves only an observability change. Decision 76 (§12.3) sets a behaviour step at 3 worlds x 5 seeds x 5000 ticks per arm, and going below it needs an owner ruling.
- Carried from the closed de-hero epic (owner #715 6875278006). Step 1's inventory also covers every place `EntityRole.HERO` or the word "hero" grants or implies behaviour. Each row gets a code citation, a one-line reason and exactly one category:
  1. a privilege to remove (no in-world basis);
  2. a capability to re-ground on real state (skills, equipment, reputation, standing), naming that state and the rule that requires it (CAUSE-04, ID-02);
  3. harmless naming, recorded and left alone.
- Open question carried, not pre-answered: is `HERO_KILL` (`src/engine/combat_rewards.py:14`, `:43`; xp 20 / gold 50 against MONSTER's 10 / 5, Bible 02 reward table) a privilege (category 1) or a difficulty signal keyed on role (category 2)?
- A row that is a rule violation rather than a preference goes to rpg-designer for a rule-level ruling. The inventory also answers whether `EntityRole.HERO` can go, or must stay as pure classification.

## Out of Scope
- §12.4 (packs, herds, territory), milestones 2 and 3, and any rule work not listed in §12.3 (owner ruling only).

## Acceptance Criteria
- The no-name-check probe finds no name switch left in a decision path.
- The camp tether is gone and the home range is declared.
- Tests for the new behaviour, plus the parity ledger and Bible updates in the same change.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20261001-EPIC-DEHERO-ROLE-GATED-PRIVILEGE-INVENTORY (adopt its HERO inventory; don't duplicate it)
- TCK-20261109-M1-NO-NAME-CHECKS-PROBE-AND-CONTENT-ALONE-KIND-PROBE

## Related Docs
- docs/plans/systemic_world/m1_kernel_spec_items_2_6.md (the kernel spec + this item's own-job counts; owner answers Q1-Q10, #715 6937049127)
- docs/plans/systemic_world/roadmap.md (§12.3 milestone 1, §12.5 done criteria)
- docs/plans/systemic_world/owner_decision_memo.md

## Related Stored Artifacts
None.

## Related Code Areas
src/strategy/, src/systems/, decision code

## Assumptions / Open Questions
- Order (roadmap §12.5, memo rows 89/93/95): the v1-disclosure repairs, then D80C, then the decision-73 step (#781, the v1.1 record), then the §12.3 items. Starting this item needs the owner's dispatch yes, brought by rpg-planner via lead-planner-u24.
- Owner-level choices are asked when the milestone starts, not guessed here.

## Implementation Notes
None yet.

## Test Summary

## Files Changed

## Completion Summary
