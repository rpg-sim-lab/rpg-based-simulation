---
status: active
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20261111-NO-RECRUITMENT-APPRAISAL-RUNS-IN-ANY-CORPUS-WORLD
artifact_type: test_plan
---

# Test plan

Measurement ticket; the "tests" are the spy rows and the hash twins. No repo test is added (no fix).

- Spy: `recruit_spy.py` (draft, sha256 sent to rpg-planner). Read-only wrappers; per-tick state scan; SHADOW verdict at each JOIN_PARTY selection.
- Cells (on HOST FREE only): 20 spied (4 worlds x s42-46 x 5000) on current main, plus 4 plain s42 twins run with the same script (`PLAIN`). A spied final hash that differs from its plain twin is a STOP.
- Counts per world and seed: (a) contracts created by site; (b) stopped before appraisal.py:83; (c) JOIN_PARTY selections and groups formed by path (cooperation accept / execute_recruit / other); (d) `_appraise_recruitment` calls (cross-check of the P1 zero); SHADOW verdicts as inputs and statuses only.
- Pass/ruling: rpg-designer's order fixed on 2026-11-11 before any rows (ticket Scope 3).

## Proof Plan
- Counts (a)-(d) per world and seed: the spy JSON of each hash-matched cell.
- Path map OFFERED to end state with file:line: investigation.md.
- Ruling recorded: rpg-designer, in the ticket.
