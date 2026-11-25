---
status: historical
layer: strategy
authority: P2
audience: agent
ticket_id: TCK-20261029-AN-ESCALATED-NEED-THAT-WINS-SCORING-LOSES-THE-PROJECT-SWITCH
artifact_type: test_plan
tags: []
---

# Test plan (written before code; the tests ship with the code)

Real-kernel tests (the strategic harness, tests/unit/strategic): an escalated hunger winner (hunger past 0.6 x 95) with a town_return project current, ACTIVE and inside its 10-tick lock, and a winner utility <= 80: takes the switch (need project current, town_return SUSPENDED with suspended_since = tick, same update); the same with a resolve_blocker current and utility > 80; the same subject with a present threat (an acting hostile in view): the ordinary comparison holds the current (no switch); a hunger winner BELOW the onset: the ordinary lock and retention hold; a fatigue winner with an escalated HUNGER project current: the ordinary comparison (the need-vs-need exclusion, pending Q1); a `detour` candidate: unchanged; an escalated need with NO current project: created as before; the suspended project resumes through the existing same-kind path.
Negative controls and mutants for the review: m1 the pressing test off (a non-escalated winner bypasses: control (c) fails); m2 the threat test off (control (b) fails); m3 the need-vs-need exclusion off (control (d) fails); m4 the bypass applied to every kind (the ordinary-kind controls fail).
Existing tests to run: tests/unit/strategic (switch, lock, STRAT-186, route_live_record, orphan, supersede), tests/unit/ai, tests/unit/engine (the actions and tactical interplay), tests/unit/tactical (SURV-07 grids), the content/parity/divergence docs tests, the code-health trio and the mypy gate. The full tests/unit in directory chunks (the observability directory per file: it segfaults in DuckDB as one process, on main too).
Measurement acceptance (HARD, designer to fix): (i) fires counted by need and current kind; (ii) K3 losses A+B = 0 on kit v6 neg; (iii) fires under a threat = 0; (iv) a cell where the rule never fires hashes equal to e39fe7873's (c1fddc5d / a383096d / c57fe53b); (v) report-only collapse lines, fix vs K2 head.
