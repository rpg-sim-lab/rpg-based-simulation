# Core Update Models

Canonical typed representations of state transitions and intents.

## Modules

| Module | Holds |
|---|---|
| `buildings.py`, `inventory.py`, `quests.py`, `resources.py` | `BuildingUpdate`, `InventoryUpdate`/`ItemInstanceUpdate`, `QuestUpdate`, `ResourceTransferIntent` |
| `social.py` | `RejectionEvent`, `SocialBondUpdate`, `SocialUpdate` |
| `strategic.py` | `StrategicUpdate` |
| `combat.py` | `CombatIntent`, `CombatUpdate`, `EquipmentUpdate`, `WoundUpdate`, `StaminaUpdate`, `StatusEffectUpdate` |
| `body.py` | `InteractionUpdate`, `TaskUpdate`, `BiologicalUpdate`, `AttributeUpdate`, `LifecycleUpdate`, `RewardUpdate` |
| `world.py` | `ResourceNodeUpdate`, `WorldUpdate`, `ChestUpdate`, `CampUpdate`, `FactionUpdate`, `ClanUpdate`, `QuestOpportunityRewardIntent`, `NO_OWNER_SENTINEL`, `decode_owner_faction_id_set` |

`src/core/updates.py` keeps `EntityUpdate`, `StateUpdate`, `NavigationUpdate` and `IdentityUpdate` (two architecture guards read it by path: `faction_set=` and `lodged_in_set/_clear=` are allowed only there) and re-exports every moved name, so callers keep importing from `src.core.updates`.
