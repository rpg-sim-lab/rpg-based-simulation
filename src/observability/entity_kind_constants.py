from __future__ import annotations

# M1 step 3: these are role labels (occupations), read from `identity.occupation`; renamed from ..._KINDS (a name only; the members are unchanged).
# Canonical producer of these labels is src/world/boss.py (check_for_boss_spawn / check_for_lair_spawn);
# living here is a deliberate interim. The two concepts must stay distinct: goblin_raider is excluded
# from spawn cadence but is not a boss kind (it has its own raid_party_spawned event).
BOSS_ENTITY_OCCUPATIONS = frozenset(("world_boss", "ancient_sentinel", "dragonkin"))

SPAWN_CADENCE_EXCLUDED_OCCUPATIONS = (None, "world_boss", "ancient_sentinel", "goblin_raider", "dragonkin")
