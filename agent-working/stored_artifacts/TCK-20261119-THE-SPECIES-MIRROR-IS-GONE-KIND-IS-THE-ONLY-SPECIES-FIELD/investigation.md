---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261119-THE-SPECIES-MIRROR-IS-GONE-KIND-IS-THE-ONLY-SPECIES-FIELD
artifact_type: investigation
tags: []
---

# Investigation
57 test files read or wrote the dead mirror; 46 failed after the src change (45 test files plus a helper). Shapes: readers `(e.identity.properties or {}).get("species_id")` (to `species_of(e)`); builders with a role-word kind plus a mirror write (to `.kind(<species>)`); test premises that depended on the mirror (presenter no-species, common_knowledge no-species hostile, occupation_field K6/K7) ruled by rpg-designer. The throwaway-copy proof (archive of 7549105d7 plus the patch) turned 45 of 45 failing files green; the owner approved the patch (#715 6985677098 / 6985692443). Statics and the 93-file regression ran on 23d6bf642.

## Measurement (S9 run, 2026-11-18, recorded on #715; evidence: executed, validated by the same_run hash cross-check)
tree_base = git archive 346c2dc78 (archive sha256 f1b5d89c3714a01e546d2969a9e99a65ac4e2b889c518f70bf84f949ad4aaf8c); tree_new = git archive 79713fae2d692e02b7b54cc94bfd61e37d906ebd (sha256 9f207615649ae67a04cd1c9ab8c5fbed4af22c872a599df769e55f771ae07779); src and tests of 79713fae equal 23d6bf642; the closure commit touches docs only. Runner run_projection_head79713fae.sh ff85555b via launcher 4a2ca09c, probe e88e69ba, compare 1bccef76; 9 processes, all rc=0, 0 guard kills; driver.log 17:49:59Z-18:51:53Z.
- K11 (neutral by projection): "K1 differing fields total: 0" on frontier_living_world, urban_political, crowded_frontier at s42 x 5000; only start_hash and final_hash differ, as allowed.
- Unprofiled needs = 0 at t0 and at the final state in all 3 worlds; the allowlist leg (world_boss, magical_demonic_entity) is NOT EXERCISED in the gate worlds (none exist there; counts {} at t0 and final), so it is not a pass: those writers are proven by unit and integration tests only. Entities t0/final: 55/55, 30/30, 38/38. Each probe final_hash equals the new arm's final_hash (same_run=yes, 3 of 3).
- tree_base 346c2dc78 is BEFORE the boss dedupe fix (#964, unmerged), so both arms carry the duplicate-boss bug: a fair A/B.
- Result shas: run_results_shas.txt 62a5fd528a63e1bd94ec4d43a86be208089d4128804db3a1ceb6c71ad5b1b0ad (per-file shas inside; k1.txt d640c12a28cc1fb6b628177ad51d9938e57e1b614e8b92fad11b4936875844d8, driver.log 9915d4e637d92fc6d62f9c13a0718fa5f74c17b3deae736f643dc768b76abc86).
- Preflight (executed, scratch copies): first table 6d4592ac (4 fails, all from the probe on tree_base, a process the run does not have; manifest split to mirror the run), arms 0/25 FAIL, probe 0/18 FAIL. Stated limits: empty import_files; missing-output FAIL covered by a unit test not yet on main.
- Run dirs for the owner delete list: tree_base, tree_new (with data/runs/rpgm_*), tree_base_prev, tree_new_360b4844, preflight_scratch, fixproof, the m1step5 cells.
- Perf (wall from driver.log timestamps, base vs new): frontier_living_world 9m46s vs 10m06s (+3%), urban_political 5m27s vs 5m22s, crowded_frontier 5m25s vs 5m28s; peak RSS equal within 11 MB (219/208, 175/176, 160/160 MB).

## Measurement note, restated after the resync (runtime-spawned wild creatures)

Neutral on the gate worlds (projection proof: K11 = 0 differing fields; the run ledger's `adds` is empty in all six accepted arms, so no `spawn_monster` call ran in 5000 ticks, and K11 does not exercise that path). A behaviour change for runtime-spawned wild creatures (`spawn_monster`: lairs `src/world/creature_territory.py:65`, camps, calamity): a body that never carried the species mirror now reads its species from `kind`, so a runtime-spawned wolf is a wild creature and obeys decision 47 like a compiled one (divergence 2.216, class Bug Fix). Only the wolf changes among the kinds `SPAWN_KIND_CATALOG_FACTION` maps to `wild_beast_pack`: slime has no diet (`body_models.yaml` `amorphous_body`), and bear, harpy and golem have no species entry. Designer ruling (a): step 5 is correct; the old test premise encoded a decision-47 breach.
