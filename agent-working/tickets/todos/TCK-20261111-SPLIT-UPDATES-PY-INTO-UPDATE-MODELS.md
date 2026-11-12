---
status: active
layer: core
authority: P1
audience: agent
ticket_id: TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS
phase: open
date: 2026-11-11
tags: []
---

# TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS

## Title
Move the per-domain update models out of src/core/updates.py into src/core/update_models/, so the module comes back under its length ceiling

## Status
OPEN

## Tier
standard

## Type
refactor

## Priority
P3

## Request Summary
This is the paydown ticket for the owner's ceiling raise (#715 6785100551, "Raise + file split ticket (Recommended)"). TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME raised the `src/core/updates.py` module-length ceiling from 1315 to 1316, for one import line. The owner's standing rule since then: a ceiling raise is accepted only with a named paydown ticket. This ticket is that row's `retiring_ticket`.

At main 5c6990e51, `updates.py` is 1315 lines, with 27 classes: the entity-level updates (Equipment, Interaction, Combat, Navigation, Task, Identity, Social, Biological, Attribute, Lifecycle, Reward, Strategic, Stamina, Wound, StatusEffect), EntityUpdate, the world and state updates (ResourceNode, World, Chest, Camp, Faction, Clan), and StateUpdate. The repo already has the pattern: `src/core/update_models/` holds buildings, inventory, quests and resources, and `updates.py` re-exports them (docs/engine/architecture.md §7, "Decoupled Core Models"; docs/core/update_intents.md, "Extension rules").

## Scope
1. Move whole classes, unchanged, into `src/core/update_models/<domain>.py`, following the existing package. A candidate grouping: combat (CombatIntent, CombatUpdate, WoundUpdate, StaminaUpdate, StatusEffectUpdate, EquipmentUpdate), social (RejectionEvent, SocialBondUpdate, SocialUpdate), body (BiologicalUpdate, AttributeUpdate, LifecycleUpdate, RewardUpdate), and world (ResourceNodeUpdate, WorldUpdate, ChestUpdate, CampUpdate, FactionUpdate, ClanUpdate, QuestOpportunityRewardIntent). The implementer settles the grouping by import cycles. EntityUpdate and StateUpdate stay in `updates.py`.
2. `updates.py` re-exports every moved name, so no caller changes. Nothing is renamed, and no field, default, merge rule or `is_noop` changes.
3. Pay the ratchet down honestly: the module-length row for `updates.py` falls to its new value, with ceiling = value. Each new module gets its own baseline rows only if a gate measures it. Remove `retiring_ticket` from the row once it is under its original ceiling.
4. Proof that nothing changed: the repo's unit suites for core, engine, social and combat; mypy_gate; `codebase.health check`; and one pinned crowded_frontier s42 5000-tick cell whose final hash equals main's. The serialised forms (`to_canonical_dict`, the checkpoint pickle) are unchanged, because the class module path is part of a pickle. Check the checkpoint round-trip test explicitly.

## Out of Scope
- Any change to merge semantics (F2, F5 and F7 of the next-generation contract spec §9 stay with that contract).
- The typed-delta work of the next-generation engine contract (child 4/5). Coordinate with architecture-planner-u24 first: if a stage there is about to reshape these classes, this ticket waits for it or folds into it.

## Acceptance Criteria
- `updates.py` is under 1315 lines, and its baseline row has ceiling = value and no `retiring_ticket`.
- Every import of a moved name still resolves; no caller is edited.
- The crowded s42 hash equals main's, and the checkpoint round-trip passes.

## Related Tickets
- TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME (the raise)
- TCK-20260326-BIGMOD (the earlier overgrown-module refactor)
- TCK-20261109-EPIC-NEXT-GENERATION-ENGINE (contract spec §3 field merge rules)

## Related Docs
- docs/engine/architecture.md §7
- docs/core/update_intents.md
- src/core/update_models/README.md

## Related Stored Artifacts
- None.

## Related Code Areas
- src/core/updates.py
- src/core/update_models/
- codebase/baselines/code_health_exceptions.jsonl (the updates.py module-length row)

## Assumptions / Open Questions
- Pickle paths: a moved class pickles under its new module. If any stored checkpoint must still load, keep a module alias or a `checkpoint_fields` step. Check this before moving anything.
- Filed by rpg-planner on 2026-11-11, from the owner ruling (#715 6785100551). Slot: after the current RPG heads; light, no paired measurement.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
