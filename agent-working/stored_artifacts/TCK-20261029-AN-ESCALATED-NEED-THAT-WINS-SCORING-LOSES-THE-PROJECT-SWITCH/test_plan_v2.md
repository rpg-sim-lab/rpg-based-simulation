---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH
artifact_type: test_plan
tags: []
---

# Test plan v2 (adds to test_plan.md; the rulings 972600b6)

Real-kernel tests: (a) an escalated hunger winner against a LOCKED town_return current with no present threat takes the switch and the current is suspended (same update); also with a resolve_blocker current; (b) the same with a present threat: no switch (the ordinary path decides); (c) an escalated hunger winner against a current FATIGUE project (and fatigue against a current hunger project), escalated or not: the ordinary path decides (the kind-identity exclusion); (d) a non-escalated hunger winner: ordinary path, unchanged; (e) `detour` unchanged; (f) no current project: created as before.
Refactor neutrality: the existing switch, lock, STRAT-186, route_live_record, orphan and supersede tests unchanged; `_ordinary_switch_allows` returns exactly what the pre-refactor `evaluate_project_switch` decided over a table of (current, candidate, lock, margin) cases; a hash-equal unit check; a TAKEN-but-ordinary-allowed case yields the same update shape as the ordinary path.
Mutants for the review: pressing test off (d fails); threat test off (b fails); kind exclusion off (c fails); rule applied to every kind (ordinary-kind controls fail).
Phase 0 kit controls: tests/tools/test_k3_phase0_kit.py, 15 pass.
