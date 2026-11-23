---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON
phase: open
date: 2026-11-23
tags: []
---

# TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON

## Title
A subject remembers why a place failed it, for what purpose, and reconsiders it by that reason (the #996 rework: an entity-owned navigation experience memory)

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner decision (#715 ask 7090468332, answers 7090493248): rework PR #996 now, around a reason-based, entity-owned experience memory, folded into Milestone 1 decision 56 (places are found from what the subject perceives, remembers or was told). The owner then approved the design with every recommendation (packet #715 7091042721, answers 7091099713; values 100 / 50 / 5 / 8 / 4).

The design is docs/plans/systemic_world/experience_memory_design.md, the authoritative spec for this ticket. The input it answers is the owner-provided external review at agent-working/stored_artifacts/TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON/external_review_experience_memory.md (commit 0c56b0722).

This ticket SUPERSEDES the suppression half of TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON. That ticket stays done as stage 1: movement give-up, the typed signal, same-tick clearing, and the propose_target gate, all kept unchanged. PR #996 closes both tickets.

## Scope
The design's stages (a)-(i), as the design doc numbers them:
- typed purpose with target;
- reason-based causes from legality's ReasonCodes;
- MemoryModel.navigation experiences, intent-scoped;
- a pure gate due-read with the gated-write latch (target_gated);
- the one review writer (the strategic consume step);
- ACCESS give-up suppression retired;
- docs and parity;
- the pre-registered check kit (h);
- the measurement (i).

Data values go in a new data file navigation_experience_settings.yaml, per the owner's answers.

## Out of Scope
- Wild food (forage, carcass, prey) as a NEED_SEVERE target: reported only (E9b).
- Society or other entity sources of experience.
- A data-driven replacement for SERVICE_KINDS. The design reuses main's existing building-kind table.

## Acceptance Criteria
- The design's pre-registered checks E1-E12, with the hard bars as the design states them (E11, plus E9 hard because Q13 = yes), and the reports R1-R4. All are written before data, in the (h) kit, at a designer-approved sha with the lead's S9.
- The static checks: every target_set is bound from purpose_of (or stored_purpose at a re-emit, or ungated_purpose at the listed own-tile writes), and gate purpose == stored purpose for every writer.
- target_gated and target_purpose are written only with the target the patch keeps.
- Determinism: hash-seed equality, canonical, checkpointed, with FIELD_RULES rows. The new fields go LAST.
- Docs:
  - divergence 2.220 rewritten;
  - KNOW-05 clause;
  - Bible ch04;
  - memory_contract amended, since the new writer is outside MemoryUpdatePhase;
  - a strategic_cognition parity P0 with a passing test_path.
- Any changed existing test expectation is an owner ask.

## Related Tickets
- TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON (stage 1, done; partly superseded)
- TCK-20261023-FREE-MEAL-REMOVED-AS-ITS-OWN-STEP-BEFORE-M1 (#995: the host queue comes first)

## Related Docs
- docs/plans/systemic_world/experience_memory_design.md (the spec)
- docs/plans/systemic_world/owner_decision_memo.md row 99 (the roadmap §12.5 change under decision 56)
- docs/plans/systemic_world/m1_kernel_spec_items_2_6.md item 4 (decision 56)
- docs/guidelines/intentional_divergences.md 2.220; docs/engine/memory_contract.md; docs/world_rules/knowledge-agency/knowledge-information.md KNOW-05

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON/external_review_experience_memory.md (owner-provided external input)

## Related Code Areas
- src/core/giveup_records.py, src/strategy/destination_suppression.py
- src/engine/movement.py (_oscillation_replan, _find_way_round_loop, _find_sidestep), src/engine/legality.py
- src/systems/strategic_systems/blocker_lifecycle.py, intelligence.py, work_queue.py
- src/core/state.py (NavigationState, MemoryModel), checkpoint FIELD_RULES
- the tactical writers listed in the design (25 gate calls, 28 target_set writes)

## Assumptions / Open Questions
- Every owner question is answered (7091099713). Anything new found during implementation goes to rpg-planner, then the lead, as an owner ask.
- Lane: rpg-implementer-3 on rpg-stalemate-nav. No pytest on u24 until the lead confirms a host gap. An S10 before each push.

## Durable state, lifecycle and clocks
New durable fields, each typed, canonical, hashed and checkpointed, LAST with FIELD_RULES rows:
- NavigationState.target_purpose
- NavigationState.target_gated
- MemoryModel.navigation (NavigationExperience records)

Lifecycle per the design: filing by the consume step, a gate due-read, a recorded review, eviction by data cap. Clocks are the explicit tick, never a getattr default.

## Implementation Notes
- Typing refinement inside the approved rule (designer, relayed by rpg-planner): the design's `need_service: Optional[str]` ("EAT" / "REST") is `need_services: FrozenSet[NeedService]` (`NeedService(str, Enum)`: EAT, REST), because an inn serves both and a compound string would be durable meaning in a string. Empty means not a food or bed tile. Canonical form is a sorted list of values. NEED_SEVERE = (EAT in need_services and hunger >= STARVING_LINE) or (REST in need_services and sleep_debt >= SLEEP_LINE). Looked up through main's `SERVICE_KINDS` table, no new name read.
- The content-matrix evidence string for `access_giveup_limit` (`src/content/matrix.py`, "strategy/blocker_settings", names `giveup_filing_update` as the runtime consumer) changes with the cutover commit, when the ACCESS filing is removed.
- `GiveUpRecord.to_canonical` carries the producer's evidence (cause, ring evidence, from-position, target tile, stored purpose) whenever the record has a from-position; `tests/unit/movement/test_giveup_records.py:105` asserts the old two-key form and goes on the class (ii) owner table, required by the approved design (section 3, #715 7091099713).
- The navigation experience settings family is `data/content/strategy/navigation_experience_settings.yaml` (100 / 50 / 5 / 8), wired through schema, repository, matrix and `src/content/navigation_experience_settings.py`.

## Test Summary

## Files Changed

## Completion Summary
