---
status: active
layer: strategy
authority: P1
audience: agent
ticket_id: TCK-20261028-LOW-HP-RETREAT-BRANCH-HOLDS-A-STARVING-SUBJECT-IN-PLACE-BESIDE-A-NON-ACTING-HOSTILE
artifact_type: investigation
---

# Investigation

- After ENG (law P) the low-hp branch is reached only without a pressing need, with an acting hostile (a real flight), or in the hunt-exemption case; `need_first` returns above it. Below 15% hp `present_threat_terms` always includes WOUNDED (hp < 0.7), so a present-threat gate there is a no-op. The defect that remains is the None destination: a no-op ENTITY_MOVE PANIC_RETREAT with RETREAT mode over the subject's own tile.
- The panic branch (:252) ran before `need_first` and froze a pressing subject with no destination below the consequence line (the gap the owner named, #715 6697215821).
- The stored nav target flips to (0,0) between decisions: intelligence.py:670 (`fused_strategic_pass`) copies the active objective's target_position; the objective belongs to a COMBAT_RETREAT project built by CombatRetreatScorer (scorers.py:248-252) with target state.town_center. In the lodging_kernel fixture town_center is the (0.0, 0.0) default; real worlds give (25,25). Base e512a40d9 walks the same way, so the hold does not unlock the held flight. Filed: TCK-20261109-A-COMBAT-RETREAT-PROJECT-WALKS-THE-SUBJECT-AGAINST-THE-HELD-FLIGHT-RULE (P2), TCK-20261109-STATE-TOWN-CENTER-DEFAULT-IS-A-SENTINEL-A-RETREAT-CAN-AIM-AT (P3).
- Scope 1 (the refusal of e38's step to (31,40) at fliving s43 t2345, file:line and ReasonCode) was NOT traced: e38 is alive at 5000t on the base and the fix in the paired cell, so by the planner's rule no trace followed.
