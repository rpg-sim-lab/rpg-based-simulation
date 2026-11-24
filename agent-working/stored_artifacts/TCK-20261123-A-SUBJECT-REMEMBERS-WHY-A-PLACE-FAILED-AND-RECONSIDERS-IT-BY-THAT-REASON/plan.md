---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON
artifact_type: plan
tags: []
---

# Plan: the #996 rework (navigation experience memory)

Spec: `docs/plans/systemic_world/experience_memory_design.md` (owner-approved, #715 7091042721 / 7091099713). This plan only orders the work. Lane: rpg-implementer-3 on `rpg-stalemate-nav`. No pytest until the lead confirms a host gap; tests are written with each commit and run only in a confirmed gap. An S10 before each push; nothing is pushed by this plan.

## Order (each step is one commit, behaviour-preserving until step 6)

1. **(a1) Fields and pure helpers, no behaviour change.** `TargetPurpose`; `NavigationState.target_purpose` and `target_gated` (LAST, FIELD_RULES rows, canonical, hashed); `NavigationUpdate.target_purpose_set` / `target_gated_set`; the patch rule that both are written only with the target the patch keeps (`anchored_target` drop path included); the pure `purpose_of`, `stored_purpose`, `ungated_purpose`. Nothing reads them yet. Tests: canonical, checkpoint round trip, old checkpoint loads None/False, patch rule (a dropped gated write beside a stored ungated hold).
2. **(a2) Every writer passes the purpose.** `propose_target` / `destination_open` gain `purpose` (before `staged`); every `target_set` write carries `target_purpose_set` bound from the same name as the gate's argument; re-emission sites carry `stored_purpose` and end the move typed on None; own-tile holds use `ungated_purpose` and write `target_gated` False. The gate itself still behaves as on the F2 head. The static (AST) check is extended: same bound name, bound from `purpose_of` / `stored_purpose` / `ungated_purpose`, mode argument consistency, helpers follow the name, no gate call without `purpose`, no new-target `target_set` without a purpose. Test: for every writer, gate purpose == stored purpose after apply.
3. **(b) Producer evidence.** `_find_way_round_loop` and `_find_sidestep` return the refusal ReasonCode per ring tile mapped to `RingEvidence`; `_oscillation_replan` builds a widened `GiveUpRecord` (cause, ring_evidence, from_position, target_tile, stored purpose); the kernel `current_tick` is passed explicitly (no `getattr(..., 0)`); a stored purpose of None files no experience (counted). `GiveUpRecord` widening is canonical and FIELD_RULES-covered.
4. **(c) The memory model and the data file.** `NavCause`, `RingEvidence`, `NavExperienceStatus`, `ReviewReason`, `NavigationExperience`, `NavigationExperienceMemory`; `MemoryModel.navigation` LAST with a FIELD_RULES row; `NavigationExperienceUpdate` plus its apply (idempotent by id and cycle, eviction order); the presenter shaping; `data/content/strategy/navigation_experience_settings.yaml` (100 / 50 / 5 / 8) loaded through the warmed catalog and part of the fingerprint. The data file moves here from (g) because (d) and (e) read it.
5. **(d1) The consume step writes experiences, additively.** Review (due records to REVIEWED), file (upsert with cycle + 1, all fields derived afresh), clear pending; `need_service` via the existing `SERVICE_KINDS` lookup (`consume_giveup_records` gains `state`). The ACCESS blocker filing and the gate's `_blocker_hit` stay for this commit, so the step is observable but changes no refusal.
6. **(e + d2 + f) The cutover, one commit.** The gate reads experiences (pending branch unchanged, then an ACTIVE same-purpose record not due and not latched); the due rule is a pure read of the subject's own tick, position and needs; the latch uses `target_gated`; the `:514` stored-target clear is purpose-scoped; the A'' third source becomes the purpose-scoped filing anchor; `_blocker_hit`, `BlockerState.giveup_count` and its FIELD_RULES row, the blocker filing, `filed_suppression_anchors` / `navigation_with_filing_anchor` and the backoff use are removed; `project_giveups` per (anchor, purpose) within one project ends that project `DESTINATION_GIVEN_UP` at `access_giveup_limit`. Doing e, d2 and f together is forced: removing the ACCESS filing removes the only thing that ended the project, so f must land with it.
7. **(g) Docs and parity.** Divergence 2.220 rewritten; KNOW-05 clause; Bible ch04; `memory_contract.md` (the new writer is outside MemoryUpdatePhase); a P0 `strategic_cognition.yaml` parity entry with a passing test_path (the F2 suppression entry marked superseded); the `blocker_settings.yaml` comment; mechanisms.yaml text comes from rpg-planner.
8. **(h) The own-job kit** (E1-E12, R1-R4, controls that bite, spy equal to its plain twin) written BEFORE any data, then to the designer, then the lead's S9. **(i)** the runs, one at a time on HOST FREE, plus the pin diff part (a) at the end of the host queue.

## Risks to raise with rpg-planner before step 2

- Existing tests call `propose_target` / `destination_open` without `purpose`, and several F2 tests assert the ACCESS-suppression behaviour this rework retires. They are F2-only and unmerged, but the rule "never edit an existing test that turns red without an owner ask" applies. I will ask for one owner ruling covering the F2 tests superseded by the design, listed by file, before touching any.
- The 10 owner-approved F2 test edits (#715 7077665927) concerned `giveup_count` and ACCESS filing; some become moot when step 6 removes them.
- Design counts 20 `propose_target(` sites at 4ab97912e; my grep counts 19 lines (+5 `destination_open(`). Reconcile in step 2 by AST, not grep; the static check is the authority.
