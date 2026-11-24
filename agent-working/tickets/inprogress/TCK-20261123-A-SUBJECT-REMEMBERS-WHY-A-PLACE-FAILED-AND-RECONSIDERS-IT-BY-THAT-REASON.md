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
- Item 2 of the #996 CI fixes (architecture-reviewer, approve with conditions): the import-contract breaks are fixed without a contract edit. `src/core/need_lines.py` is the one source of the starving line (95.0) and the sleep line (98.0); `StarvationTable.starving_line` takes its default from it, `need_pull.HUNGER_LINE` points at it (it was a second copy of the same 95.0), and `SLEEP_LINE`/`STARVING_LINE` stay importable from the engine modules. `need_services` is read by the producer at the give-up (`movement.need_services_at`) and carried on `GiveUpRecord.need_services` (last field, canonical list of sorted values); the consume step takes no `state`. **Deliberate behaviour note:** the needs are now frozen at give-up time, not at consume time (the next strategic pass, a few ticks later), so a building that appears or vanishes in that window is no longer seen. The worker packet and the serial state give the same needs (`tests/unit/movement/test_need_services_at.py`).
- Digest (a75144d9e): `GiveUpRecord.to_canonical` hashes every field always, so the old "bare record keeps its two-key form" rule is gone; this is the owner-approved `test_giveup_records.py:105` change (an owner ask via the lead).

- Step (b) (14437545a): `tests/unit/movement/test_need_services_at.py:48` expects the enum values `["EAT","REST"]` (the design §6 and the note above already use upper case); my own new test had the wrong casing.
- Step (e), the ACCESS cutover per the owner-approved table c9969877 (#715 7122160427), source 381a646bc and tests 3a255035a: the gate (`destination_suppressed`) reads pending records (any purpose) then ACTIVE experiences of the same purpose that are not due (`due_reason`, pure) and not latched (stored target gated, near the anchor, same stored purpose), minus the reviews the staged update carries; a staged upsert does not refuse in its own pass. `_blocker_hit`, `SuppressionHit.giveup_count`, `BlockerState.giveup_count`, its FIELD_RULES row, the `:g<n>` fingerprint part and the presenter key are removed. `giveup_filing_update` became `giveup_project_end_update` (ends the current project when an upsert's `project_giveups` reaches `access_giveup_limit`; files no blocker). `filed_suppression_anchors` / `navigation_with_filing_anchor` take the experience update and ride an anchor only when the stored target purpose equals the record's. Text: the schema description, the matrix evidence string (matrix doc regenerated), the `blocker_settings.yaml` comment. The 24 table rows are in 3a255035a (rows 21-24 mechanical) with a fixture helper `tests/unit/strategic/experience_fixture.py`.
- Off-table fixture conversions (setup only, assertions unchanged; rpg-planner sent items 1-3 to the lead as S8): (1) `test_notice_suppressed_goal_stands.py` and (2) `test_objective_destination_suppressed.py` (293ec5f8f); (3) the blocker-fixture tests inside `test_propose_target.py` (the proposal point, three flight tests, the executor's typed end, MOVE_TO); (4) `test_the_fused_pass_that_files_an_experience_returns_its_anchor_without_a_clear` in `test_giveup_clear_and_service.py`: the scenario is restated (the record has a purpose and the subject holds a far stored target of the same purpose) because the approved same-purpose anchor rule needs it. **Item 4 is PENDING the lead's classification**; if refused, only that test is reverted. (5) row 20's test renamed `..._is_the_pre_f2_string`, as the table says.
- Step (g) (98050a531), text only: `registries/mechanisms.yaml`, the mechanism verification view (generated), Bible chapter 04 (2.220 section), `intentional_divergences.md` 2.220 (an amendment bullet), parity rows STRAT-356 and COMB-359. The parity-ledger schema ratchet shows 2 falls (combat_movement `allOf/2/else/then/properties/test_path/type` 261 to 259); left untightened (rpg-planner clears any baseline edit).
- First-run risks (step (e) tests are WRITTEN, NOT RUN at the time of this note): (a) the gate now loads the warmed catalog (`navigation_experience_settings()`) on the first call that has both a purpose and a stored experience, so the new gate tests load it; calls without a purpose or without records return before that; (b) a give-up whose stored purpose is None files no experience, so it counts toward `project_giveups` never (design §3), and a test or run that expects the old per-anchor count for such a give-up will differ.
- Item 4 of the off-table fixtures is S8 per #715 7123276232 (which covers all four); the `:105` widening by one key (`need_services`) is the owner's answer #715 7123267511.
- S8 notes of the first test run on c59f73220: (a) row 6 and its sibling ("another purpose is not cleared") get a purpose-less far pending record `GiveUpRecord((90,90),3)`, the file's own slow-path forcing, because an active experience alone raises no work-queue tier (owner #715 7123503340; row 6's asserts unchanged). (b) `test_wider_scope_numbers_pinned` 384/270 to 385/271: `src/core/need_lines.py` (item 2) is a new in-scope, unbound file (S8 #715 7123495747). (c) The engine count 1303 (+3 skipped) is the intended removal of the `giveup_count` FIELD_RULES row (its parametrized id `test_an_append_named_in_field_rules_passes_the_check[giveup_count]`); confirmed on #715.
- Known gap (design section 4 tier argument; owner #715 7123503340): a calm subject holding a stored target near an active experience of the same purpose keeps it until it is served or makes its next choice.
- A full spot is not a failed spot (owner #715, option 1 "a full spot is not a failed spot" (asked as #715 7126061322)): `MovementSystem._oscillation_replan` (movement.py) returns the give-up WITHOUT a record when `LegalityServiceV2.get_occupant(target_tile, ..., ignore_entity_id=entity.id)` finds another body on the target tile; the target is dropped and the typed give-up written as before. New tests `tests/unit/movement/test_giveup_held_tile.py` (held / free pairs for the oscillation and the ring-blocked cause, the target tile and not the ring, the turn-taking scene with its free-tile control, determinism); the scenes were checked once with a read-only python script (not pytest) before the gap; no existing expectation was edited. Docs: design 2.1, mechanisms.yaml (+ view), Bible ch04, divergence 2.220 amendment 2, parity STRAT-356/COMB-359. Known limit: ring crowding around a free tile still files; the post-fix run measures it.

## Test Summary

## Files Changed

## Completion Summary
