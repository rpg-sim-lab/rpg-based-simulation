---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED
tags: []
---

# investigation - TCK-20261031-AN-ENGAGEMENT-OVERRIDES-A-PRESSING-NEED

## Findings so far
- Lane B's skip counter recorded 0 over 131785 evaluate calls. Cause found: `TacticalDecisionSystem.evaluate_entity_intent(state, entity, neighbors=None, region_trauma=None)`; the wrapper in f3h_obs.py read `entity = a[0]`, `state = a[1]` (swapped), so `present_threat(entity, state)` raised inside a bare `except`, before `_SKIP[...] += 1`. Not a binding problem: `classify_neighbours` is imported into tactical's namespace and the patch works.
- Smoke (urban_political s44, 50 ticks, probe `eng_probe.py`): the fixed counter records hostiles-present calls (16 of 131 evaluate calls).
- Skip sites (tactical.py, to be completed with tests in the report): the `if not hostiles:` block at tactical.py:266 (objective pursuit incl. building arrival/hunger arrival, role obligation) is skipped on ANY hostile (presence test: classify_neighbours hostiles); `in_place_survival_update` (tactical_rest.py:135) calls rest_in_place_update / eat_carried_update / eat_at_corpse_in_place_update, the corpse one yields to present_threat_terms (tactical_rest.py:109).
