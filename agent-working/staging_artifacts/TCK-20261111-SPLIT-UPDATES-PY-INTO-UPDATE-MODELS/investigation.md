---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS
artifact_type: investigation
phase: open
date: 2026-11-12
tags: []
---

# Investigation

## Starting state
`src/core/updates.py` at origin/main 5e58ae857: 1316 lines, 27 classes plus `decode_owner_faction_id_set`, `_merged_spawn_sources`, `NO_OWNER_SENTINEL`, `_LIFECYCLE_SET_FIELDS`, `EMPTY_ENTITY_UPDATE`. Module-length baseline row: ceiling 1316, `retiring_ticket` this ticket.

## Dependencies between the classes (AST)
Only CombatUpdate (refs CombatIntent, EquipmentUpdate, SocialUpdate, StrategicUpdate, WoundUpdate), SocialUpdate (SocialBondUpdate), EntityUpdate (15 entity-level updates) and StateUpdate (the world updates, EntityUpdate, RejectionEvent) reference other classes. No cycle once EntityUpdate and StateUpdate stay.

## Path-keyed guards (why four classes stay)
`faction_set=` is allowed only in `src/core/updates.py` (IdentityUpdate); `lodged_in_set/_clear=` only in `core/updates.py` (NavigationUpdate).

## Pickle and checkpoint grep
- `pickle` appears in `src/engine/scenario_checkpoint.py` (`pickle.dumps(state)` / `pickle.loads`), `src/core/state.py` (comments about positional unpickle of AuthoritativeState) and `tools/knowledge_search.py` (unrelated).
- What is pickled is `AuthoritativeState` only. `src/core/state.py` names no update record except the type name `StateUpdate`, which stays in `updates.py`. No update record is stored in a checkpoint, and no module path of a moved class is pickled.
- Checkpoint tests on the trial move: `test_scenario_checkpointer.py`, `test_checkpoint_fields.py`, `test_checkpoint_group_fields.py`, `test_beds_survive_a_checkpoint_restore.py`: 27 passed.
- Moved classes now report `__module__ = src.core.update_models.<x>`; callers import through `src.core.updates`, which re-exports them.

## Ratchet finding
`codebase.health check` reads a moved function or file-keyed ruff count as a NEW row in the new file (findings.py:28 says that is accepted, but the check still blocks). After fixing substance (docstrings, one import, the sentinel move) 4 rows remain: body.py C901 1, combat.py C901 1, PLR0912 1, complexipy CombatUpdate.merge 30. Their counterparts in updates.py are gone or lower at an equal total (C901 6 = 4+1+1, PLR0912 5 = 4+1). Awaiting the lead's baseline ruling.

## Mover bug caught
The first run left `NO_OWNER_SENTINEL` (an AnnAssign) in `updates.py`, so `decode_owner_faction_id_set` in `world.py` had an undefined name. Found by ruff F821; fixed by moving the constant with its comment block.
