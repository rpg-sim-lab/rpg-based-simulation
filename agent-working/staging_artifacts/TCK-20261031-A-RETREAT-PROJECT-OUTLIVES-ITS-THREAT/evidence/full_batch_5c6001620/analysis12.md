# Death bar (full)

## Per world and cause, per seed (base/fix), totals, tier

| world | cause | s42 | s43 | s44 | s45 | s46 | base total | fix total | threshold | seeds rising | tier |
|---|---|---|---|---|---|---|---|---|---|---|---|
| urban_political | HAZARD | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 10 | 10 | +2 | 0 | - |
| urban_political | COMBAT | 3/3 | 4/4 | 2/2 | 6/7 | 4/4 | 19 | 20 | +2 | 1 | TIER 2 |
| urban_political | DEFEAT | 3/4 | 2/2 | 2/2 | 8/7 | 4/5 | 19 | 20 | +2 | 2 | TIER 2 |
| crowded_frontier | HAZARD | 3/2 | 5/11 | 5/5 | 3/3 | 6/6 | 22 | 27 | +3 | 1 | TIER 2 |
| crowded_frontier | COMBAT | 21/21 | 18/14 | 18/18 | 21/21 | 11/11 | 89 | 85 | +9 | 0 | - |
| crowded_frontier | DEFEAT | 11/11 | 10/9 | 10/10 | 12/12 | 5/5 | 48 | 47 | +5 | 0 | - |
| frontier_living_world | HAZARD | 9/9 | 9/9 | 9/9 | 13/13 | 3/3 | 43 | 43 | +5 | 0 | - |
| frontier_living_world | COMBAT | 13/13 | 9/8 | 17/17 | 7/7 | 17/17 | 63 | 62 | +7 | 0 | - |
| frontier_living_world | DEFEAT | 3/3 | 3/2 | 6/5 | 8/8 | 11/11 | 31 | 29 | +4 | 0 | - |

- urban_political all three causes: base 48, fix 50 (RISE)

- crowded_frontier all three causes: base 159, fix 159

- frontier_living_world all three causes: base 137, fix 134

TIER 1 STOPs: none
TIER 2 pairs: [('urban_political', 'COMBAT'), ('urban_political', 'DEFEAT'), ('crowded_frontier', 'HAZARD')]

## Tier 2 / Tier 1 extra victims (fix-arm death of this cause, entity not dead of this cause on base): first diff, path, mechanism test

- urban_political COMBAT s45: base 6 fix 7; run first diff {'base': (185, 16, True, 'proj_combat_engage_164'), 'fix': (182, 19, True, '')}
    - e16 died t474 COMBAT attacker 10; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_ACT mode MovementMode.REGROUP reason None action ATTACK project proj_combat_engage_464; entry tick t463 pos [29.0, 32.0] move ENTITY_ACT reason None mode MovementMode.REGROUP project  writer project/other (no tactical reason)
      base fate: died t454 DEFEAT attacker 4; fix project path last 60t: [(417, '-'), (425, 'proj_combat_engage_424'), (455, '-'), (465, 'proj_combat_engage_464'), (475, 'proj_combat_engage_464')]; base path: [(417, '-'), (425, 'proj_combat_engage_424'), (455, 'proj_combat_engage_424')]
- urban_political DEFEAT s42: base 3 fix 4; run first diff {'base': (263, 26, True, ''), 'fix': (263, 18, True, '')}
    - e14 died t466 DEFEAT attacker 22; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.RETREAT reason PANIC_RETREAT action None project proj_combat_engage_466; entry tick t455 pos [17, 32] move ENTITY_ACT reason None mode MovementMode.REGROUP project proj_combat_engage_406 writer project/other (no tactical reason)
      base fate: died t446 COMBAT attacker 7; fix project path last 60t: [(407, 'proj_combat_engage_406'), (457, '-'), (467, 'proj_combat_engage_466')]; base path: [(407, 'proj_combat_engage_406'), (447, 'proj_combat_engage_406')]
- urban_political DEFEAT s46: base 4 fix 5; run first diff {'base': (169, 12, True, 'proj_combat_retreat_88'), 'fix': (169, 12, True, 'proj_resolve_blocker_168')}
    - e3 died t277 DEFEAT attacker 17; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.RETREAT reason PANIC_RETREAT action None project ; entry tick t266 pos [33.0, 27.0] move ENTITY_ACT reason None mode MovementMode.REGROUP project proj_resolve_blocker_237 writer project/other (no tactical reason)
      base fate: alive at end; fix project path last 60t: [(218, '-'), (238, 'proj_resolve_blocker_237'), (248, '-'), (258, 'proj_resolve_blocker_237'), (268, '-'), (278, '-')]; base path: [(218, '-'), (238, 'proj_resolve_blocker_237'), (248, '-'), (258, 'proj_resolve_blocker_237'), (268, '-'), (278, 'proj_resolve_blocker_237')]
    - e13 died t627 DEFEAT attacker 14; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.RETREAT reason PANIC_RETREAT action None project ; entry tick t621 pos [36.0, 40.0] move ENTITY_MOVE reason None mode MovementMode.PURSUE project  writer project/other (no tactical reason)
      base fate: alive at end; fix project path last 60t: [(628, '-')]; base path: []
- crowded_frontier HAZARD s43: base 5 fix 11; run first diff {'base': (145, 16, True, 'proj_combat_engage_124'), 'fix': (142, 19, True, '')}
    - e13 died t370 HAZARD attacker None; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.INTERCEPT reason INTERCEPTING action None project proj_combat_engage_347; entry tick t370 pos [44.0, 41.0] move ENTITY_MOVE reason INTERCEPTING mode MovementMode.INTERCEPT project proj_combat_engage_347 writer src/engine/tactical.py:612
      base fate: died t1480 COMBAT attacker 35; fix project path last 60t: [(328, 'proj_resolve_blocker_327'), (348, 'proj_combat_engage_347'), (371, 'proj_combat_engage_347')]; base path: [(328, 'proj_resolve_blocker_327'), (348, '-'), (368, 'proj_resolve_blocker_327')]
    - e32 died t538 HAZARD attacker None; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.REGROUP reason REGROUP action None project ; entry tick t538 pos [44.0, 42.0] move ENTITY_MOVE reason REGROUP mode MovementMode.REGROUP project  writer src/engine/tactical.py:382
      base fate: died t1128 DEFEAT attacker 30; fix project path last 60t: [(479, '-'), (539, '-')]; base path: [(489, '-'), (509, 'proj_resolve_blocker_508')]
    - e5 died t542 HAZARD attacker None; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.REGROUP reason REGROUP action None project proj_combat_engage_535; entry tick t542 pos [44.0, 43.0] move ENTITY_MOVE reason REGROUP mode MovementMode.REGROUP project proj_combat_engage_535 writer src/engine/tactical.py:382
      base fate: died t943 COMBAT attacker 30; fix project path last 60t: [(496, '-'), (516, 'proj_resolve_blocker_515'), (536, 'proj_combat_engage_535'), (543, 'proj_combat_engage_535')]; base path: [(496, 'proj_resolve_blocker_295'), (516, '-'), (536, 'proj_resolve_blocker_535')]
    - e8 died t555 HAZARD attacker None; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.REGROUP reason REGROUP action None project proj_resolve_blocker_532; entry tick t555 pos [44.0, 42.0] move ENTITY_MOVE reason REGROUP mode MovementMode.REGROUP project proj_resolve_blocker_532 writer src/engine/tactical.py:382
      base fate: alive at end; fix project path last 60t: [(513, '-'), (533, 'proj_resolve_blocker_532'), (556, 'proj_resolve_blocker_532')]; base path: [(513, '-'), (533, 'proj_resolve_blocker_532')]
    - e2 died t1310 HAZARD attacker 17; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.REGROUP reason REGROUP action None project ; entry tick t1310 pos [42.0, 51.0] move ENTITY_MOVE reason REGROUP mode MovementMode.REGROUP project  writer src/engine/tactical.py:382
      base fate: died t317 COMBAT attacker 36; fix project path last 60t: [(1311, '-')]; base path: []
    - e6 died t1315 HAZARD attacker None; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.WANDER reason REGROUP action None project proj_resolve_blocker_1274; entry tick t1315 pos [42.0, 41.0] move ENTITY_MOVE reason REGROUP mode MovementMode.WANDER project proj_resolve_blocker_1274 writer src/engine/tactical.py:382
      base fate: died t1637 COMBAT attacker 35; fix project path last 60t: [(1255, '-'), (1275, 'proj_resolve_blocker_1274'), (1316, 'proj_resolve_blocker_1274')]; base path: [(1295, '-'), (1315, 'proj_resolve_blocker_1314')]
    - e4 died t1361 HAZARD attacker 14; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.WANDER reason REGROUP action None project proj_hunger_1336; entry tick t1361 pos [40.0, 44.0] move ENTITY_MOVE reason REGROUP mode MovementMode.WANDER project proj_hunger_1336 writer src/engine/tactical.py:382
      base fate: alive at end; fix project path last 60t: [(1317, '-'), (1337, 'proj_hunger_1336'), (1362, 'proj_hunger_1336')]; base path: [(1337, '-'), (1357, 'proj_resolve_blocker_1356')]

## Tactical chase into drain terrain (HAZARD victims, all fix-arm HAZARD deaths): entry writer counts, so the older INTERCEPTING/BRACKETING defect is not counted against retention

- urban_political base: HAZARD deaths by entry-move reason {None: 9, 'REGROUP': 1}
- urban_political fix: HAZARD deaths by entry-move reason {None: 9, 'REGROUP': 1}
- crowded_frontier base: HAZARD deaths by entry-move reason {None: 15, 'PANIC_RETREAT': 1, 'INTERCEPTING': 2, 'BRACKETING': 3, 'AVOID_HOSTILE': 1}
- crowded_frontier fix: HAZARD deaths by entry-move reason {None: 13, 'INTERCEPTING': 2, 'REGROUP': 8, 'BRACKETING': 3, 'AVOID_HOSTILE': 1}
- frontier_living_world base: HAZARD deaths by entry-move reason {'PANIC_RETREAT': 1, 'INTERCEPTING': 3, 'REGROUP': 10, 'KEEP_DISTANCE': 4, None: 22, 'FLEE_THREAT': 2, 'AVOID_HOSTILE': 1}
- frontier_living_world fix: HAZARD deaths by entry-move reason {'PANIC_RETREAT': 1, 'INTERCEPTING': 3, 'REGROUP': 10, 'KEEP_DISTANCE': 4, None: 22, 'FLEE_THREAT': 2, 'AVOID_HOSTILE': 1}

## Reported only: per-seed rises inside a (world, cause) whose 5-seed total did not rise (victim ids; no PASS/FAIL/NOT SHOWN review)

