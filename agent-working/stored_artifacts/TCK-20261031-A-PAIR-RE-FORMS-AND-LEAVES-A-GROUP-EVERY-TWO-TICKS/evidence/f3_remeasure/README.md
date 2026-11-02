---
status: active
layer: simulation
authority: P1
audience: agent
artifact_type: report
ticket_id: TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS
phase: open
date: 2026-11-01
tags: []
---

# Re-measure on F3: set C, probes and traces (evidence index)

Base tree = origin/main 30307228c (F3 landed). Arm tree = effd2e8fc (the churn fix merged onto it). Host: ubuntu, cores 4-5, one run at a time, audit mode for C and the traces,
`PYTHONHASHSEED=0`. Scratch trees and the raw per-run json stay in `/data/vboxuser/Work/groups_base/` (`trees/30307228c`, `trees/effd2e8fc`, `out15F/` = the 30 C runs as json, `out_decF/`
= the four probe json, `out_t2/`, `out_e23/`, `out_e30/`, `out_occ/`, `out_trace_lodge/`, `out_hashF/`, `out_decF/`). `.json` files are not committed (the repository ignores them under
`stored_artifacts`). Since the trim (owner ruling #715 6573916118) the raw files are out of git too: the per-tick traces (`traces/`, 11 `.jsonl` files; 5 small ones that other tickets cite stay in git: the e10 rows and trust run, both e23 traces, the frontier s45 trace; the other 6 are listed with bytes and sha256 in `../README_raw_data.md`) are kept under `/data/vboxuser/Work/groups_base/raw_evidence/` (same relative path). The run logs under `logs/` were never in git (`*.log` is ignored); they stay on disk in `/data/vboxuser/Work/groups_base/*.log`. Committed here: the scripts, the READMEs and the text summaries.

## Layout

| Path | What |
|---|---|
| `logs/` (on disk only, not in git) | `run15F.log`, `run15F_urban.log` (C), `hashF.log` (3 pinned hash runs on f6cd0e057), `ctlL.log` (lodger-row control), `D.log` (seed 0 vs 1), probe/trace run logs |
| `scripts/` | the wrappers and drivers (`m15.py`, `m15_dec.py`, `trace_*.py`, `*.sh`, `outside_follow.py` with its planted-state test, `decan.py`, `t2sum.py`, `t2scan.py`) |
| `summaries/` | C world-end reports; probe summaries (decision rows by kind and change within 10 ticks, leaves, DEFEAT rows); outside-follower and contract rows (urban s42); Tier 2 per-victim rows and range-entry scans |
| `traces/` (5 cited small files in git; the rest out: see `../README_raw_data.md`) | per-tick traces: `f43_*.jsonl` (frontier s43 e12/e6), `e30/`, `e23/` (urban s42 both arms), `tier2/` (crowded s43, frontier s45, urban s44; crowded s43 e10/e27 and trust runs), `occ/` (occupancy and retreat probe) |

## What was run (all hash-neutral wrappers; no src change)

- C: 15 paired runs, 3 worlds x seeds 42-46 x 2000t. Tier 1 not fired in any world; hard law `{}` on all 30 runs; lag 0. Two lodger STOPs at world end: frontier s43 e12 (DEFEAT t1433) and urban s42 e23 (COMBAT t1687).
- Probes on the arm, hash equal to the unprobed arm run: frontier s43 3498ddfaad4e, s44 ebc58e3b8c34, s45 ae53a2935364; urban s42 d327ea389dbf. Frontier probes lack the contract rows and the outside-follower count (added after s45 started); urban s42 carries them.
- Traces: frontier s43 e12/e6 (pair), e30 tactical trace, urban s42 e23/e24 (pair), Tier 2 (crowded s43, frontier s45, urban s44), crowded s43 e10/e27 and trust, urban s42 occupancy and retreat probe. Each trace's death list equals C's up to its stop tick.

## Corrections made along the way (the final wording to use)

- DISSOLVED rows in the frontier s45 probe: 10, not 8 (the earlier message's 8 was a mis-sum).
- e23 (urban s42): e17, its killer, did NOT hold e23 as its target throughout. At t1669 its target is 18; at t1681 it picks 23 from adjacent [23, 5, 24] on hp 32. e17's first pick of 23 is at t1663 on distance (7 against 8 for e5), with group_bias 1.0 for both candidates. The e23 verdict: NOT FED on item 1, NOT FED by the recast (iii) test, designer's final word pending.
- Base e23: in the base run entity 23 is dead since t111 (HAZARD), so the base trace has no e23 in the window t1630-1700; the "extra victim" for e23 is by (entity, cause) and there is no same-tick base comparison for it.
- e12 (frontier s43): the chain "group shared target -> e12 drops FATIGUE -> INTERCEPTING" was reversed in the first report; e12 (leader) picks e30 at t1399 with the group's shared target still None and the shared target becomes 30 at t1400 from e12's own pick; FATIGUE persists through the first intercept and the first hit at t1404. The first working verdict was NOT SHOWN, before the leave rows; the final ruling (rpg-designer) is NOT FED, e12 cleared.
- Frontier base lodged-at-decision counts for s43, s44, s45 are 0, 0, 0 (arm 70, 738, 1192); "4, 176, 86" is crowded_frontier's row.
- s44 formations: in g10082 (formed 1892) entity 4, the group's other member, leaves its bed at state tick 1898 (plain rest end); the chosen leader/holder entity 1 stays lodged. In g10048 (urban s42, formed 1671) entity 3 leaves at 1674 (plain rest end).
- `AVOID_NO_ROUTE` is not a route search and not tile occupancy: it is `retreat_destination` returning None (no region contains the tile and no home region; geometry only), identical at [41,30] and [41,31].
- Verdicts after the traces (rpg-designer / rpg-planner): e12 NOT FED, cleared. e22 (frontier s45): FED by the letter of (i), limit disclosed. e23 (urban s42): NOT FED on item 1, NOT FED by the recast (iii) test, designer's final word pending. e10 (crowded s43): fix-fed. The other Tier 2 victims are not read as fed.
- The group counter work is separate: `next_group_id` is a non-optional int default 10000 seeded only by restore (FIELD_RULES) and checked there (`GroupCounterBehindStoreError`); restore checks the spec id before the fill.

## Limits that apply to every row

- Tactical-call traces see only the `evaluate_entity_intent` calls the hook caught (the function is called rarely per entity); absence of a row is not absence of a decision.
- "Writer" of a leave is what the task became (a plain rest end for every leave traced), not the upstream system that wrote it.
- Trust values: e10 against leader 4 = 0.8 from bonds (sentiment 0.6); (1 - 0.8) x 0.5 = 0.1 equals the tuple's group_bias.
