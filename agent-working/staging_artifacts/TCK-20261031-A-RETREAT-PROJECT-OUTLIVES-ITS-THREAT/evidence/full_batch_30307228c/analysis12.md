# Death bar (full)

## Per world and cause, per seed (base/fix), totals, tier

| world | cause | s42 | s43 | s44 | s45 | s46 | base total | fix total | threshold | seeds rising | tier |
|---|---|---|---|---|---|---|---|---|---|---|---|
| urban_political | HAZARD | 2/2 | 2/2 | 2/2 | 2/2 | 2/2 | 10 | 10 | +2 | 0 | - |
| urban_political | COMBAT | 3/3 | 4/4 | 2/2 | 6/7 | 4/4 | 19 | 20 | +2 | 1 | TIER 2 |
| urban_political | DEFEAT | 3/4 | 2/2 | 2/2 | 8/7 | 4/5 | 19 | 20 | +2 | 2 | TIER 2 |
| crowded_frontier | HAZARD | 3/2 | 5/7 | 5/5 | 5/5 | 4/4 | 22 | 23 | +3 | 1 | TIER 2 |
| crowded_frontier | COMBAT | 20/19 | 14/16 | 16/16 | 16/17 | 16/16 | 82 | 84 | +9 | 2 | TIER 2 |
| crowded_frontier | DEFEAT | 11/11 | 13/13 | 13/13 | 10/11 | 8/8 | 55 | 56 | +6 | 1 | TIER 2 |
| frontier_living_world | HAZARD | 9/9 | 9/9 | 7/7 | 14/14 | 3/3 | 42 | 42 | +5 | 0 | - |
| frontier_living_world | COMBAT | 13/13 | 9/8 | 15/16 | 7/7 | 18/18 | 62 | 62 | +7 | 1 | - |
| frontier_living_world | DEFEAT | 3/3 | 3/2 | 11/11 | 7/7 | 11/11 | 35 | 34 | +4 | 0 | - |

- urban_political all three causes: base 48, fix 50 (RISE)

- crowded_frontier all three causes: base 159, fix 163 (RISE)

- frontier_living_world all three causes: base 139, fix 138

TIER 1 STOPs: none
TIER 2 pairs: [('urban_political', 'COMBAT'), ('urban_political', 'DEFEAT'), ('crowded_frontier', 'HAZARD'), ('crowded_frontier', 'COMBAT'), ('crowded_frontier', 'DEFEAT')]

## Tier 2 / Tier 1 extra victims (fix-arm death of this cause, entity not dead of this cause on base): first diff, path, mechanism test

- urban_political COMBAT s45: base 6 fix 7; run first diff {'base': (185, 16, True, 'proj_combat_engage_164'), 'fix': (182, 19, True, '')}
    - e16 died t473 COMBAT attacker 4; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_ACT mode MovementMode.REGROUP reason None action ATTACK project proj_combat_engage_464; entry tick t462 pos [29.0, 32.0] move ENTITY_ACT reason None mode MovementMode.REGROUP project  writer project/other (no tactical reason)
      base fate: died t454 DEFEAT attacker 4; fix project path last 60t: [(417, '-'), (425, 'proj_combat_engage_424'), (455, '-'), (465, 'proj_combat_engage_464'), (474, 'proj_combat_engage_464')]; base path: [(417, '-'), (425, 'proj_combat_engage_424'), (455, 'proj_combat_engage_424')]
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
- crowded_frontier HAZARD s43: base 5 fix 7; run first diff {'base': (145, 16, True, 'proj_combat_engage_124'), 'fix': (142, 19, True, '')}
    - e13 died t370 HAZARD attacker None; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.INTERCEPT reason INTERCEPTING action None project proj_combat_engage_347; entry tick t370 pos [44.0, 41.0] move ENTITY_MOVE reason INTERCEPTING mode MovementMode.INTERCEPT project proj_combat_engage_347 writer src/engine/tactical.py:612
      base fate: died t1177 DEFEAT attacker 30; fix project path last 60t: [(328, 'proj_resolve_blocker_327'), (348, 'proj_combat_engage_347'), (371, 'proj_combat_engage_347')]; base path: [(328, 'proj_resolve_blocker_327'), (348, '-'), (368, 'proj_resolve_blocker_327')]
    - e11 died t485 HAZARD attacker None; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.PURSUE reason None action None project ; entry tick t485 pos [45.0, 41.0] move ENTITY_MOVE reason None mode MovementMode.PURSUE project  writer project/other (no tactical reason)
      base fate: died t960 COMBAT attacker 30; fix project path last 60t: [(470, '-'), (486, '-')]; base path: [(430, '-')]
    - e31 died t522 HAZARD attacker None; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.PURSUE reason None action None project proj_combat_engage_509; entry tick t522 pos [44.0, 41.0] move ENTITY_MOVE reason None mode MovementMode.PURSUE project proj_combat_engage_509 writer project/other (no tactical reason)
      base fate: died t894 COMBAT attacker 30; fix project path last 60t: [(470, 'proj_fatigue_409'), (510, 'proj_combat_engage_509'), (523, 'proj_combat_engage_509')]; base path: [(470, 'proj_combat_engage_469'), (490, '-'), (510, 'proj_fatigue_409')]
    - e1 died t524 HAZARD attacker None; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.PURSUE reason None action None project proj_combat_engage_519; entry tick t524 pos [45.0, 40.0] move ENTITY_MOVE reason None mode MovementMode.PURSUE project proj_combat_engage_519 writer project/other (no tactical reason)
      base fate: alive at end; fix project path last 60t: [(510, '-'), (520, 'proj_combat_engage_519'), (525, 'proj_combat_engage_519')]; base path: [(500, 'proj_resolve_blocker_299'), (520, '-')]
- crowded_frontier COMBAT s43: base 14 fix 16; run first diff {'base': (145, 16, True, 'proj_combat_engage_124'), 'fix': (142, 19, True, '')}
    - e34 died t422 COMBAT attacker 28; holding retreat at death: True; retreats adopted in window [(347, 'proj_combat_retreat_346'), (423, 'proj_combat_retreat_346')]; THREAT_CLEARED in window []; OUTCOME PASS: retreat proj_combat_retreat_346 was current on the entry move into the death tile at t421 (move reason PANIC_RETREAT, writer src/engine/tactical.py:222) -> STOP to the designer with this chain
      death detail: at death task ENTITY_MOVE mode MovementMode.RETREAT reason PANIC_RETREAT action None project proj_combat_retreat_346; entry tick t421 pos [104.0, 34.0] move ENTITY_MOVE reason PANIC_RETREAT mode MovementMode.RETREAT project proj_combat_retreat_346 writer src/engine/tactical.py:222
      base fate: died t276 DEFEAT attacker 16; fix project path last 60t: [(423, 'proj_combat_retreat_346')]; base path: []
    - e36 died t461 COMBAT attacker 3; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.RETREAT reason PANIC_RETREAT action None project proj_recover_104; entry tick t461 pos [30, 41] move ENTITY_MOVE reason PANIC_RETREAT mode MovementMode.RETREAT project proj_recover_104 writer src/engine/tactical.py:222
      base fate: died t484 DEFEAT attacker 8; fix project path last 60t: [(405, 'proj_recover_104'), (462, 'proj_recover_104')]; base path: [(415, '-'), (425, 'proj_combat_engage_424')]
    - e15 died t601 COMBAT attacker 38; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_ACT mode MovementMode.REGROUP reason None action None project ; entry tick t590 pos [41.0, 40.0] move ENTITY_ACT reason None mode MovementMode.REGROUP project  writer project/other (no tactical reason)
      base fate: died t776 DEFEAT attacker 30; fix project path last 60t: [(566, '-'), (602, '-')]; base path: []
    - e17 died t625 COMBAT attacker 38; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_ACT mode MovementMode.REGROUP reason None action None project ; entry tick t614 pos [40.0, 40.0] move ENTITY_MOVE reason PANIC_RETREAT mode MovementMode.RETREAT project  writer src/engine/tactical.py:222
      base fate: died t213 DEFEAT attacker 34; fix project path last 60t: [(626, '-')]; base path: []
    - e8 died t778 COMBAT attacker 30; holding retreat at death: True; retreats adopted in window [(773, 'proj_combat_retreat_772'), (779, 'proj_combat_retreat_772')]; THREAT_CLEARED in window []; OUTCOME PASS: retreat proj_combat_retreat_772 current at death t778 (task ENTITY_ACT) -> STOP to the designer with this chain
      death detail: at death task ENTITY_ACT mode MovementMode.REPOSITION reason None action ATTACK project proj_combat_retreat_772; entry tick t767 pos [27, 35] move ENTITY_ACT reason None mode MovementMode.REPOSITION project  writer project/other (no tactical reason)
      base fate: died t1571 DEFEAT attacker 38; fix project path last 60t: [(753, '-'), (773, 'proj_combat_retreat_772'), (779, 'proj_combat_retreat_772')]; base path: [(753, '-'), (773, 'proj_resolve_blocker_772')]
    - e10 died t940 COMBAT attacker 30; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.RETREAT reason PANIC_RETREAT action None project ; entry tick t932 pos [11, 38] move ENTITY_MOVE reason PANIC_RETREAT mode MovementMode.RETREAT project  writer src/engine/tactical.py:222
      base fate: died t298 HAZARD attacker 14; fix project path last 60t: [(881, '-'), (941, '-')]; base path: []
    - e9 died t1340 COMBAT attacker 30; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_ACT mode MovementMode.RETREAT reason None action None project proj_town_return_351; entry tick t1340 pos [11.0, 11.0] move ENTITY_ACT reason None mode MovementMode.RETREAT project proj_town_return_351 writer project/other (no tactical reason)
      base fate: died t1261 DEFEAT attacker 38; fix project path last 60t: [(1341, 'proj_town_return_351')]; base path: []
    - e6 died t1415 COMBAT attacker 30; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_ACT mode MovementMode.RETREAT reason None action None project ; entry tick t1404 pos [10.0, 39.0] move ENTITY_ACT reason None mode MovementMode.REGROUP project  writer project/other (no tactical reason)
      base fate: alive at end; fix project path last 60t: [(1416, '-')]; base path: []
    - e37 died t1990 COMBAT attacker 30; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_ACT mode MovementMode.RETREAT reason None action None project proj_fatigue_1463; entry tick t1989 pos [40.0, 39.0] move ENTITY_MOVE reason PANIC_RETREAT mode MovementMode.RETREAT project proj_fatigue_1463 writer src/engine/tactical.py:222
      base fate: alive at end; fix project path last 60t: [(1991, 'proj_fatigue_1463')]; base path: [(1934, '-'), (1944, 'proj_hunger_1243'), (1954, '-'), (1964, 'proj_fatigue_1723'), (1984, 'proj_hunger_1243')]
- crowded_frontier COMBAT s45: base 16 fix 17; run first diff {'base': (814, 7, True, 'proj_recover_813'), 'fix': (814, 7, True, '')}
    - e32 died t1212 COMBAT attacker 30; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.RETREAT reason PANIC_RETREAT action None project ; entry tick t1201 pos [26.0, 41.0] move ENTITY_ACT reason None mode MovementMode.RETREAT project  writer project/other (no tactical reason)
      base fate: died t1380 HAZARD attacker 30; fix project path last 60t: [(1213, '-')]; base path: []
    - e36 died t1533 COMBAT attacker 30; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_ACT mode MovementMode.REGROUP reason None action None project ; entry tick t1526 pos [25.0, 16.0] move ENTITY_MOVE reason BRACKETING mode MovementMode.REPOSITION project  writer src/engine/tactical.py:557
      base fate: alive at end; fix project path last 60t: [(1475, '-'), (1485, 'proj_resolve_blocker_1444'), (1499, '-'), (1505, 'proj_resolve_blocker_1444'), (1515, '-'), (1534, '-')]; base path: [(1475, '-'), (1485, 'proj_fatigue_1464'), (1487, '-'), (1505, 'proj_fatigue_1464'), (1515, '-'), (1525, 'proj_fatigue_1464')]
    - e35 died t1601 COMBAT attacker 15; holding retreat at death: False; retreats adopted in window []; THREAT_CLEARED in window []; OUTCOME FAIL: no retreat adopted or completed within 200t -> divergence, reported
      death detail: at death task ENTITY_MOVE mode MovementMode.RETREAT reason PANIC_RETREAT action None project proj_hunger_1245; entry tick t1601 pos [37.0, 40.0] move ENTITY_ACT reason None mode MovementMode.RETREAT project proj_hunger_1245 writer project/other (no tactical reason)
      base fate: alive at end; fix project path last 60t: [(1546, 'proj_hunger_1245'), (1556, '-'), (1566, 'proj_hunger_1245'), (1602, 'proj_hunger_1245')]; base path: [(1546, 'proj_hunger_1245'), (1566, 'proj_town_return_1445'), (1576, '-'), (1586, 'proj_town_return_1445')]
- crowded_frontier DEFEAT s45: base 10 fix 11; run first diff {'base': (814, 7, True, 'proj_recover_813'), 'fix': (814, 7, True, '')}
    - e7 died t1580 DEFEAT attacker 15; holding retreat at death: False; retreats adopted in window [(1414, 'proj_combat_retreat_1173')]; THREAT_CLEARED in window []; OUTCOME FAIL: retreat adopted [(1414, 'proj_combat_retreat_1173')] / THREAT_CLEARED [] within 200t, but the entry move into the death tile (t1579, project proj_hunger_1513, reason None) and the death task were not selected by it: trajectory only (it changed who fought or where), divergence, reported
      death detail: at death task ENTITY_ACT mode MovementMode.PURSUE reason None action None project proj_hunger_1513; entry tick t1579 pos [30.0, 32.0] move ENTITY_MOVE reason None mode MovementMode.PURSUE project proj_hunger_1513 writer project/other (no tactical reason)
      base fate: alive at end; fix project path last 60t: [(1534, '-'), (1554, 'proj_hunger_1513'), (1564, '-'), (1574, 'proj_hunger_1513'), (1581, 'proj_hunger_1513')]; base path: [(1534, 'proj_town_return_973')]

## Tactical chase into drain terrain (HAZARD victims, all fix-arm HAZARD deaths): entry writer counts, so the older INTERCEPTING/BRACKETING defect is not counted against retention

- urban_political base: HAZARD deaths by entry-move reason {None: 9, 'REGROUP': 1}
- urban_political fix: HAZARD deaths by entry-move reason {None: 9, 'REGROUP': 1}
- crowded_frontier base: HAZARD deaths by entry-move reason {None: 14, 'PANIC_RETREAT': 3, 'INTERCEPTING': 3, 'BRACKETING': 1, 'REGROUP': 1}
- crowded_frontier fix: HAZARD deaths by entry-move reason {None: 16, 'INTERCEPTING': 2, 'BRACKETING': 1, 'REGROUP': 1, 'PANIC_RETREAT': 3}
- frontier_living_world base: HAZARD deaths by entry-move reason {'PANIC_RETREAT': 1, 'INTERCEPTING': 3, 'REGROUP': 10, 'KEEP_DISTANCE': 4, None: 20, 'FLEE_THREAT': 3, 'AVOID_HOSTILE': 1}
- frontier_living_world fix: HAZARD deaths by entry-move reason {'PANIC_RETREAT': 1, 'INTERCEPTING': 3, 'REGROUP': 10, 'KEEP_DISTANCE': 4, None: 20, 'FLEE_THREAT': 3, 'AVOID_HOSTILE': 1}

## Reported only: per-seed rises inside a (world, cause) whose 5-seed total did not rise (victim ids; no PASS/FAIL/NOT SHOWN review)

- frontier_living_world COMBAT s44: base 15 -> fix 16; fix-only victims (entity, tick) [(16, 984), (52, 1707)]
