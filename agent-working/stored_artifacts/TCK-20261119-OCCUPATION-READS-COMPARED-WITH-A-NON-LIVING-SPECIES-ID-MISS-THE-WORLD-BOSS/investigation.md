---
status: historical
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261119-OCCUPATION-READS-COMPARED-WITH-A-NON-LIVING-SPECIES-ID-MISS-THE-WORLD-BOSS
artifact_type: investigation
tags: []
---

# Investigation: occupation reads compared with a non-living species id

Base: origin/main a30847030. Method: search_docs and `graphify query` first, then an AST scan of every `src/*.py` compare (script outside the repo, read-only), then a text scan of every src line that mentions "occupation" beside a quoted species id.
Species ids considered: the 14 in `data/content/living/species.yaml` plus the two keys of `NON_LIVING_KIND_ALLOWLIST` (`src/core/species.py:24`): `world_boss`, `magical_demonic_entity`.

## Direct hits (an occupation read compared with an allowlist id): 2, both fixed

| file:line | what it compared |
|---|---|
| `src/systems/world_systems/navigation.py:41` | `e.identity.occupation == "world_boss"` (the dynamic-boss fallback of `FlowFieldService.get_flow_direction`) |
| `src/world/threat.py:30` | `e.identity.occupation == "world_boss" and e.lifecycle.active and e.combat.alive` (`ThreatService.process_threat_evolution`, `has_boss`) |

Both now read `species_of(e) == "world_boss"` (the threat clause keeps its active and alive conditions).

Correction to the ticket text: the reads never matched a **boss.py-spawned** boss (species `world_boss`, occupation `ancient_sentinel`, boss.py:151-152). A **calamity-spawned** boss (`src/world/calamity.py:83`, species `world_boss`, occupation `world_boss`) DID match them.
`get_flow_direction`'s fallback is also unreachable for the `WORLD_BOSS` target while `FlowFieldService.ANCHORS` carries a fixed `WORLD_BOSS` waypoint pair, so the navigation site is dead code today; its regression test removes that pair to reach the reader.

## Reported, NOT fixed (membership in a named set that holds a species id): 4, pinned in the scan test

All four read an occupation against `BOSS_ENTITY_OCCUPATIONS` or `SPAWN_CADENCE_EXCLUDED_OCCUPATIONS` (`src/observability/entity_kind_constants.py:7,9`), which mix the species ids `world_boss` and `dragonkin` with occupations (`ancient_sentinel`, `goblin_raider`).

| file:line | compare |
|---|---|
| `src/observability/event_shapers.py:1172` | `occupation in self._BOSS_KINDS` (`_BOSS_KINDS = BOSS_ENTITY_OCCUPATIONS`, line 1134) |
| `src/observability/event_shapers.py:1207` | `occupation_of(e) not in SPAWN_CADENCE_EXCLUDED_OCCUPATIONS` |
| `src/observability/extraction/resources.py:88` | `occupation_of(e) not in SPAWN_CADENCE_EXCLUDED_OCCUPATIONS` |
| `src/observability/extraction/world.py:114` | `occupation in BOSS_ENTITY_OCCUPATIONS` |

They work for boss.py bosses only through the occupation `ancient_sentinel` in the same set. Ruling (rpg-designer u24, H2 (a)/(b)): reported, not fixed, here; the follow-up P3 rpg-planner (u24) files covers them.

## Reverse direction (an entity kind compared with an occupation-only literal): 0 hits

## Writers that give an occupation a species id (not comparisons, not touched)

- `src/world/calamity.py:83` occupation `world_boss` (species `world_boss`)
- `src/world/boss.py:265` occupation `dragonkin` (species `dragonkin`, the lair occupant)
- `src/systems/world_systems/generator.py:325` occupation `goblin` (a file this ticket must not touch)
- `src/certification/scenarios.py:74` species `goblin`, occupation `monster`

## Neighbours

- `src/world/boss.py:215` `_is_active_living_lair_occupant` already reads `species_of(entity) == "dragonkin"`.
- `tests/unit/core/test_occupation_label_readers.py::test_k5_*` is the inverse scan (an entity `kind` compared with a label); the new scan sits beside it and reuses its `_is_entity_kind` helper.
- `tests/architecture/name_switch_allowlist.yaml` rows for navigation.py and threat.py (reason "finds entities whose kind is 'world_boss'") now describe what the code does; both architecture tests stay green.
