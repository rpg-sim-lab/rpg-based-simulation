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

## Pre-registered reading (designer, 2026-11-11, before any rows)
- Spy approved at sha256 84482e13212460c4f1427efaa6020f9e566b8cf60ed0e84a4c023e4af68ccd15; 4 PLAIN s42 twins first, each spied cell passes its twin hash (exit 3 = STOP); a crash in the shadow block is a failed cell.
- (ii) holds only if a_execute_recruit_calls = 0 and b_appraise_contract_recruitment = 0 in all 20 cells plus the code-read citation of action_router.py:63-64 as the only dispatch; any execute_recruit call makes that world MIXED or DEFECT.
- BY DESIGN WITH A PARITY GAP follow-up is docs and ledger only (SOC-001, SOC-008 to divergent; one wording for the two strategic_cognition rows; ch07 "Current play" note; intentional_divergences entry, class Bounded). Code routing accepts through the appraisal is an owner row.
- Contract status flips on one id are reported unfiltered (possible copies in two dicts).
