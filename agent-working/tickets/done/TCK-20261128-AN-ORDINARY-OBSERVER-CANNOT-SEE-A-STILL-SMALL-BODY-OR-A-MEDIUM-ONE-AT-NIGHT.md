---
status: historical
layer: world
authority: P1
audience: agent
ticket_id: TCK-20261128-AN-ORDINARY-OBSERVER-CANNOT-SEE-A-STILL-SMALL-BODY-OR-A-MEDIUM-ONE-AT-NIGHT
phase: done
date: 2026-11-28
tags: [cognition]
---

# TCK-20261128-AN-ORDINARY-OBSERVER-CANNOT-SEE-A-STILL-SMALL-BODY-OR-A-MEDIUM-ONE-AT-NIGHT

## Title
An ordinary observer can't see a still small body at any distance, or a still medium one at night beyond touch: calibrate the perception gate (PERC 3a).

## Status
DONE

## Tier
standard

## Type
bug

## Priority
P1

## Request Summary
Filed by rpg-planner on 2026-11-28. HARD, M1 (rpg-designer ruling drafts/rpg-designer-perc-gate-calibration-ruling.md, sha256 4015c410), found by PERC-02b's probe (TCK-20261117-DECISIONS-SEE-OTHER-BODIES-ONLY-THROUGH-PERCEPTION, executed; perc02b_gap/probe_c.out).
The cause is a structural cap in the 02a gate (inspected): score = sense × signal × (1 − 0.02·d) × terrain × (0.5 + 0.5·alertness), threshold 0.2. perception_signals gives a small body visibility "low" (0.3), and baseline vision is "medium" (0.6), so the best case is 0.18 < 0.2. A still goblin, spider or small plant-eater is never seen by an ordinary observer at any distance; only touch at distance 1. At night vision drops 2 rungs to low (0.3), so a still medium body gets 0.3 × 0.6 = 0.18 too, and is seen only at touch.
Probe facts: a still small goblin at Chebyshev 2 is not perceived by day (conf 0.0); a still medium hostile at night is perceived only at d = 1, and by day at 1-6.
This is a common-sense violation already on main. PERC-02b would spread it to every decision, so this lands BEFORE PERC-02b's own-job run.

## Scope
- Calibrate the gate so the ACs hold. Lane proposes the data values; rpg-designer approves them before code.
- Move the threshold, distance fall-off, night steps and size/visibility levels to data/ (sim settings belong in data).
- A table test, Bible ch04 / world rule PERC-02 / parity / divergence text.

## Out of Scope
- Stealth, weather (separate tickets).

## Acceptance Criteria
- AC1 (day, baseline observer, still target, no touch): small perceived at >= 4 tiles, medium at >= 8, large at >= 12; not at 40.
- AC2 (night, no night_vision): still medium AND small perceived at >= 2 (touch already covers 1); moving targets further via noise, as today.
- AC3: size order kept: large > medium > small at the same distance.
- AC4: the threshold, fall-off, night steps and size levels live in data/, loaded and validated.
- Measured signal (own-job): perceived hostiles/prey plus hunts and engagements started, 3 gate worlds s42 1000 t, base vs fix. A collapse to 0 = STOP.

## Related Tickets
- TCK-20261117-DECISIONS-SEE-OTHER-BODIES-ONLY-THROUGH-PERCEPTION (3b; its S3/S4 rows become strict xfail citing this ticket and flip when this lands)
- TCK-20261117-EACH-BODY-PERCEIVES-BY-ITS-SPECIES-SENSES-AND-SIGNALS-FOLLOW-THE-BODY (02a, the gate's origin)
- overlap scan: search_docs not run at filing; none known.

## Related Docs
- docs/world_rules/ (PERC-02), docs/mechanics/04_strategic_cognition.md

## Related Stored Artifacts
- /mnt/data2/rpg-measure/perc02b_gap/probe_c.py, probe_c.out; reds_outside_owner_list.md (b478c253)

## Related Code Areas
- src/world/perception/gate.py, perception_signals, src/engine/appraisal.py (perceives)

## Assumptions / Open Questions
- Run hashes move on every world (more bodies perceived); no golden pins expected (as in births), and any pin that moves = an owner ask.

## Durable state, lifecycle and clocks
- None new (data-file settings only).

## Implementation Notes
Option C (designer-approved): threshold 0.15, falloff 0.04, floor 0.05, night_vision_steps 2, size_visibility {small: medium_high, medium: high, large: very_high}, all in `data/content/perception/perception_settings.yaml`, loaded and validated (`src/content/perception_settings.py`, `PerceptionSettingsDefinition`, catalog one-record family). `PerceptionGate` reads `gate.settings`; `emitted_signals` takes the size map; load validation keeps the threshold above the still-body ceiling (0.135) at the default alertness. Divergence 2.229, parity STRAT-360, ch04, PERC-02 note, content usage matrix row, known limits. Option C was chosen because lowering only the threshold would open still hearing and smell (calibration table, perc02b_gap/calib_table.out). 02a row reversal approved by the owner (#715 7237767905): seen by day at 3, unseen at 14, unseen at night at 3, plus the four two-tile rows. Written at close.

## Test Summary
Perception calibration (Option C), 3 gate worlds × s42 × 1000 t, BASE ac759e0ba → FIX bbce8de04 (#715 GO 7238294011; designer read 52d4175e; kit on evidence/perception-gate-calibration-kit @ 9622465db):
- hash-valid, no STOP;
- perceived rose in all 3 worlds (+65%, +4%, +42%);
- still-body night vision rose (49→783, 429→1075, 0→1191), and small-body day vision is newly non-zero (0→158, 0→162, 0→0);
- engagements 144→97 (crowded_frontier, unattributed; follow-up TCK-20261128-ATTRIBUTE-THE-CROWDED-FRONTIER-ENGAGEMENT-DROP-AFTER-THE-PERCEPTION-CALIBRATION), 129→222, 69→85;
- not exercised: hunts in every world, and prey pairs in crowded_frontier and urban_political;
- NOT MEASURED: bodies_hit (a kit off-by-one);
- PERF flag 1.13 and 1.12 (frontier_living_world, urban_political), crowded 1.02.

Gap on bbce8de04 (executed, scoped; not the full suite): tools chunks 0-7 all green (774, 782, 777, 647, 695, 1367, 724, 720 passed); unit content 324, worldbuilding 436, world 679, tactical 119, engine 1441 passed; tests/architecture 261; mechanism registry 155; code health OK (no new or worse blocking), import contracts 17 kept 0 broken, packages 0 problems, mypy clean. New: tests/unit/world/test_perception_calibration.py (table test of the ACs, validation, size order, data loading).

## Files Changed
data/content/perception/perception_settings.yaml; src/content/{perception_settings,schema,repository,matrix}.py; src/world/perception/gate.py; src/engine/{perception_signals,behavior_consumers}.py; registries/mechanisms.yaml; docs (known_limitations, intentional_divergences 2.229, ch04, content_usage_matrix, perception.md, parity STRAT-360); tests (test_perception_calibration, test_perc02a_senses_signals_night, test_perc02a_review_night_clock_and_lodging, test_surv07_hunt_project_grid, test_content_hotpath_guard, mechanism registry completeness pin 389). The measurement kit is NOT in this change: evidence/perception-gate-calibration-kit @ 9622465db.

## Completion Summary
Perception calibration (Option C), 3 gate worlds × s42 × 1000 t, BASE ac759e0ba → FIX bbce8de04 (#715 GO 7238294011; designer read 52d4175e; kit on evidence/perception-gate-calibration-kit @ 9622465db):
- hash-valid, no STOP;
- perceived rose in all 3 worlds (+65%, +4%, +42%);
- still-body night vision rose (49→783, 429→1075, 0→1191), and small-body day vision is newly non-zero (0→158, 0→162, 0→0);
- engagements 144→97 (crowded_frontier, unattributed; follow-up TCK-20261128-ATTRIBUTE-THE-CROWDED-FRONTIER-ENGAGEMENT-DROP-AFTER-THE-PERCEPTION-CALIBRATION), 129→222, 69→85;
- not exercised: hunts in every world, and prey pairs in crowded_frontier and urban_political;
- NOT MEASURED: bodies_hit (a kit off-by-one);
- PERF flag 1.13 and 1.12 (frontier_living_world, urban_political), crowded 1.02.

AC1-AC4 hold in the table test (day: small seen at >= 4, medium >= 8, large >= 12, not at 40; night: still medium and small seen at >= 2; size order large > medium > small; settings in data/, loaded and validated). Known limits (docs/engine/known_limitations.md): the hunt path is not exercised at 1000 t, the engagement shift is unattributed, the perf cost is about 12%. 3b (PERC-02b) rebases onto this branch; its S3/S4 strict xfails flip to pass here.
