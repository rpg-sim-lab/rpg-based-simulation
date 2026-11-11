---
status: historical
layer: systems
authority: P2
audience: agent
ticket_id: TCK-20261111-NO-RECRUITMENT-APPRAISAL-RUNS-IN-ANY-CORPUS-WORLD
artifact_type: plan
---

# Plan

Investigation only; no fix (ticket Scope 4). Order, fixed by rpg-planner's dispatch of 2026-11-11:

1. Staging artifacts first (this file, investigation.md, test_plan.md).
2. Code read (read-only): every OFFERED to ACTIVE / CANCELLED / other end-state path for a RECRUITMENT contract on main with file:line; every caller of `_appraise_recruitment`; the 2026-09-12 investigation line on whether the appraisal was reached before the wiring; what Bible ch07 and the parity ledger state about recruitment acceptance. Recorded in investigation.md.
3. Write the spy (`recruit_spy.py`, Scope 1 a-d, plus the SHADOW verdict because `appraise_contract` is pure on main: shown in investigation.md). Draft only; sent to rpg-planner for rpg-designer approval at a sha256. NOT run, NOT smoked.
4. Cells only on rpg-planner's HOST FREE: 20 spied cells on current main (crowded_frontier, urban_political, frontier_living_world, highland_traverse x s42-46 x 5000 ticks) plus 4 plain s42 twins; each spied final hash must equal its plain twin or the batch STOPs. One heavy process at a time, results under /mnt/data2/rpg-measure/recruit.
5. Rows, path map and the designer's ruling (DEAD / BYPASS BY DESIGN (i)-(iv) / BYPASS AS DEFECT / BY DESIGN WITH A PARITY GAP / MIXED) are recorded in the ticket. A fix, if any, is a new ticket.

Out of scope: tuning acceptance (D-09); re-measuring P1; the lodger and many-contracts todos (cited only).
