---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261111-SPLIT-UPDATES-PY-INTO-UPDATE-MODELS
artifact_type: plan
phase: open
date: 2026-11-12
tags: []
---

# Plan

Owner approval: #715 6813227854 (dispatch), paydown for the ceiling raise #715 6793483728 / 6785100551. rpg-planner approved this file map.

## File map (whole classes move unchanged; `updates.py` re-exports every moved name)

Stays in `src/core/updates.py`: EntityUpdate, StateUpdate (+ `_merged_spawn_sources`, `EMPTY_ENTITY_UPDATE`), NavigationUpdate, IdentityUpdate. Two guards read the file by path: `tests/architecture/test_faction_mutation_write_paths.py` (`faction_set=` only in `src/core/updates.py`, IdentityUpdate) and `tests/unit/engine/test_lodged_in_stays_in_the_apply_path.py` (`lodged_in_set/_clear=` only in `core/updates.py`, NavigationUpdate). Their allowlists are not touched.

Moves to `src/core/update_models/`:
- `social.py`: RejectionEvent, SocialBondUpdate, SocialUpdate
- `strategic.py`: StrategicUpdate
- `combat.py`: CombatIntent, EquipmentUpdate, CombatUpdate, WoundUpdate, StaminaUpdate, StatusEffectUpdate (imports social, strategic, resources)
- `body.py`: InteractionUpdate, TaskUpdate, BiologicalUpdate, AttributeUpdate, `_LIFECYCLE_SET_FIELDS`, LifecycleUpdate, RewardUpdate
- `world.py`: ResourceNodeUpdate, WorldUpdate, `NO_OWNER_SENTINEL` (with its comment block), `decode_owner_faction_id_set`, ChestUpdate, CampUpdate, QuestOpportunityRewardIntent, FactionUpdate, ClanUpdate

## Method
1. A text-preserving mover script (kept in scratch) cuts the class source by AST line spans (decorators and leading comments included) and writes each new module with only the imports it uses. Annotated module constants must be handled too (the first run missed `NO_OWNER_SENTINEL`; the AST name check caught it).
2. Fix the substance of the new-module lint rows (module/class/method docstrings, one undefined-name import); do not touch the moved complexity (C901/PLR0912 in body.py and combat.py, complexipy CombatUpdate.merge = 30): refactoring those would be a logic change.
3. Baseline: no edit until the lead or owner rules on the 4 re-keyed complexity rows.

## Out of scope
Any logic change, merge-semantics change, executor or kernel edit (C5's executor/kernel parity concern touches that area), guard allowlist edit.
