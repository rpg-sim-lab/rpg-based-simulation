---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261123-A-SUBJECT-REMEMBERS-WHY-A-PLACE-FAILED-AND-RECONSIDERS-IT-BY-THAT-REASON
artifact_type: test_plan
tags: []
---

# Test plan: the #996 rework

Tests go with each commit. No pytest runs until the lead confirms a host gap; then serially, no `-n`, one domain at a time. Bars E1-E12 and R1-R4 are the design's own-job checks (kit step (h)), pre-registered before any data.

| step | tests (new unless noted) |
|---|---|
| a1 | canonical / hash / checkpoint round trip of `target_purpose` and `target_gated`; old checkpoint loads None / False; patch rule: a dropped gated write beside a stored ungated hold leaves `target_gated` False and the purpose unchanged; `purpose_of` effective-mode cases (stored HOLD reset to WANDER, staged project, no mode) |
| a2 | for every writer, planted subject with and without stored HOLD, with and without staged project and mode: gate purpose == stored purpose after apply; extended AST check with mutants (missing purpose, different name, unbound name, helper not following the name, new-target `target_set` without purpose); re-emission with None ends typed |
| b | ring evidence per ReasonCode (BODIES / STATIC / OTHER); RING_BLOCKED vs OSCILLATION; stored purpose None files nothing and is counted; `current_tick` absent raises |
| c | model canonical, sorted by id, round trip, old checkpoint loads empty; upsert idempotent by id and cycle; review applies only to the stored cycle and ACTIVE; eviction order (reviewed oldest, due active, oldest active counted); settings file warmed and in the fingerprint; presenter shapes it |
| d1 | review sets REVIEWED with the first holding reason; file creates cycle 1 / cycle + 1 with every due field derived afresh; nothing from the old timing survives; `need_service` EAT / REST / None through `SERVICE_KINDS` |
| cutover | each due rule (OSCILLATION, BODIES, STATIC never time-due, OTHER, NEED_SEVERE at the lines); gate is pure (no update returned, probe calls spend nothing); latch only for a gated acceptance; purpose-scoped :514 clear; `project_giveups` ends the project at 4 per (anchor, purpose); no ACCESS blocker filed for a give-up; A'' purpose-scoped filing anchor; failing controls for each |
| g | parity entry test_path passes; docs consistency tests |
| h / i | kit controls that bite; spy equals plain twin; E7 hashseed identity (STOP); the rest as the design's table |

Existing tests that turn red (the F2 ACCESS-suppression and `giveup_count` tests) are NOT edited without an owner ruling; the list is sent to rpg-planner first.
Not run so far: everything above.
