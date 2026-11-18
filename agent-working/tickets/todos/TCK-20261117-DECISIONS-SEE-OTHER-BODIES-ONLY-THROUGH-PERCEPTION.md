---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261117-DECISIONS-SEE-OTHER-BODIES-ONLY-THROUGH-PERCEPTION
phase: open
date: 2026-11-17
tags: []
---

# TCK-20261117-DECISIONS-SEE-OTHER-BODIES-ONLY-THROUGH-PERCEPTION

## Title
Decisions see other bodies only through perception, and 'coming for me' reads observable intent only (PERC-02b)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
PERC-02b, the second half of TCK-20261109-M1-HONEST-PERCEPTION-DEFAULTS: one perceived_neighbours(subject, state, radius=10) query, every decision read of another body through it, and observable intent only.

## Scope
1. perceived_neighbours(subject, state, radius=10) = radius pre-filter, sense gate, saliency top-k; each site keeps its current radius.
2. Move the ~13 decision reads of another body (and the sites 02a left day-by-default) onto it; list each site's audit verdict (decision read vs build/arrival read) in the PR body; misfits go to rpg-planner as ticket candidates.
3. _coming_for drops the task-payload read: it closed the distance on its last step, or hit within the existing hit window (the constant the hit-acting predicate uses).
4. The run-ledger sampler uses the same query.
5. Divergence 2.211, ledger STRAT-353.

## Out of Scope
- Stealth and concealment; weather's perception multiplier (unread today; it stays unread).
- Balance tuning (Phase 3).

## Acceptance Criteria
- P1: decision-path reads of another body that bypass perceived_neighbours: 0 (static allowlist test).
- P4: a 'coming for me' verdict that read another body's task: 0 (static plus unit).

## Related Tickets
- TCK-20261109-M1-HONEST-PERCEPTION-DEFAULTS (parent)
- TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY (02a, lands first; this branch stacks on it)

## Related Docs
- docs/plans/systemic_world/m1_kernel_spec_items_2_6.md (Item 3)
- docs/world_rules/knowledge-agency/perception.md (PERC-02, on main with the planner's docs PR)

## Related Stored Artifacts
None.

## Related Code Areas
src/world/perception/, src/engine/appraisal.py, src/engine/hostility.py, src/engine/tactical*.py, data/content/living/

## Assumptions / Open Questions
None open; rulings by rpg-designer relayed by rpg-planner 2026-11-17 (split into 02a/02b; derive at read; unprofiled fixtures counted).

## Implementation Notes
Filed with 02a's PR; stacked on 02a.

## Test Summary

## Files Changed

## Completion Summary
