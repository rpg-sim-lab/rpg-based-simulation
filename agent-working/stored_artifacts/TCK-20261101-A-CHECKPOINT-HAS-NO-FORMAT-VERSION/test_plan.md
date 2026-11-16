---
status: active
layer: engine
authority: P1
audience: agent
ticket_id: TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION
artifact_type: test_plan
---

# Test plan — TCK-20261101-A-CHECKPOINT-HAS-NO-FORMAT-VERSION

New file `tests/unit/engine/test_checkpoint_schema.py` (unit; real `AuthoritativeState` from `lodging_kernel` plus a state with groups):
1. headerless refused: raises `CheckpointSchemaMissingError` (a ValueError); `pickle.loads` patched to raise, never called.
2. order: headerless AND spec_id mismatch -> the spec_id error, not the schema error; schema mismatch with matching spec -> schema error.
3. insert, reorder, rename, removal on a slotted record (header edited from the current schema) -> each `CheckpointSchemaMismatchError` naming class and change kind; `pickle.loads` not called.
4. appended field with a FIELD_RULES row: accepted and filled (through restore with the RecordingKernel pattern); appended field with no row: refused.
5. removed/renamed class in the header: refused; header-named non-`src.` module: refused without import.
6. current checkpoint round-trips byte-equal: save payload == payload after load+fill+re-dump; header schema identical.
7. recorder guard: classes met by `Unpickler.find_class` on the payload (dataclasses only) == header classes, on a state with entity, building, bound group, project, combat; recorder bytes == `pickle.dumps` bytes.
8. every FIELD_RULES row's `(record, field)` is a real field of that class in the current schema.
9. route: schema errors -> 400 with the shaped detail; a plain ValueError still a string.
Re-pointed (assertions unchanged): test_checkpoint_group_fields.py :119 :146 :215 :224; test_scenario_checkpointer.py :55-73. Existing slow round-trip tests (`@pytest.mark.slow`) run unchanged as the real-writer check; I will run them pinned to cores 4-5 only if you allow a tick run (the dispatch says unit only, so I will not).
Commands: `pytest tests/unit/engine/test_checkpoint_schema.py tests/unit/engine/test_checkpoint_group_fields.py tests/unit/engine/test_checkpoint_fields.py tests/unit/engine/test_scenario_checkpointer.py tests/unit/api -k "checkpoint or restore" -m "not slow"`; plus tools tests the push guard needs.
