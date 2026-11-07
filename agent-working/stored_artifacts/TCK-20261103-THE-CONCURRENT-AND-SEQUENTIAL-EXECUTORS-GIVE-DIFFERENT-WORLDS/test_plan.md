---
status: active
layer: engine
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS
tags: []
---

# test_plan - TCK-20261103-THE-CONCURRENT-AND-SEQUENTIAL-EXECUTORS-GIVE-DIFFERENT-WORLDS

Fast (tests/unit/kernel/test_executor_context_parity.py): wander target equal for state and packet; feature_flags, building_tiles, town_center, clans carried; the guard raises for an undeclared state field, passes AttributeError for others, honours the allow-list; the pass-through surfaces from execute_batch; other exceptions still no-op and are counted (positive control through the silent chunk path); join/leave clan equal on both executors.
Long (tests/integration/kernel, extra_slow): concurrent twice + sequential once on gate worlds/seeds, hashes every 100 ticks, first mismatch named, cognition by content (timeline excluded), no-op count == 0; shown red on pre-fix src.
Pins: sequential hashes (crowded s45 base 8b765653afa3 @2000, a556f1782800 @2050, eaf87b24aa7a @2100) unchanged.
