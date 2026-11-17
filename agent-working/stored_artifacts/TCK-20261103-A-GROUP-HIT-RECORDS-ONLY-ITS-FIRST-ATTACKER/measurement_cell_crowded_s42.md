---
status: active
layer: combat
authority: P1
audience: agent
ticket_id: TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER
phase: open
date: 2026-11-15
tags: []
---

# Measurement cell: crowded_frontier s42, 2000 ticks, base vs fix (rpg-designer #634 6883569761)

Run 2026-11-15 on the ubuntu host by `rpg-implementer-ubuntu`, under lead-planner's run go, one run at a time, `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0`, `taskset -c 4-5`, `PYTHONHASHSEED=0`, audit_mode and no frame pacing (`tools.test_architecture.rpg_gate_run.build_kernel`).
Driver `/data/vboxuser/Work/groups_base/measure_gh/run_cell.sh` (stops on any non-zero rc). Spy `group_hit_spy.py` in this folder (read-only; wraps `resolve_multi_attack` and `MovementSystem.resolve_move`, returns the real results unchanged).

- Base arm: `origin/main` 5ba65854c, a `git archive` at `/data/vboxuser/Work/groups_base/measure_gh/base`.
- Fix arm: this worktree at d6c9a7f8f. THE FIX ARM CARRIES BOTH TICKETS (the group-hit record and the `target_score` term); the cell does not separate them.
- Raw files (JSON, not committed because `.json` is dropped by gitignore): `/data/vboxuser/Work/groups_base/measure_gh/crowded_s42/{base,fix}_{plain,spy}.json`, the logs beside them and `run.out`.

## Runs
| run | rc | wall | peak (scope MemoryPeak, 5 s samples) |
|---|---|---|---|
| base plain | 0 | 175 s | 237 MB |
| base spied | 0 | 176 s | 260 MB |
| fix plain | 0 | 191 s | 265 MB |
| fix spied | 0 | 185 s | 278 MB |

Plain-twin checks: base spied 8596e6b3ac1c = base plain; fix spied a4f356e8d890 = fix plain. 0 exceptions. data/runs: the count is 663 before and after; the runners removed their own run dirs. No run dir of this cell remains.

## Hash
Fix is not hash-equal to base: base 8596e6b3ac1c; fix (flat-sha256-v5) a4f356e8d890; the fix state hashed in v4 form 432f8d1ae5a0. The fix changed this cell, and its trajectory diverges from base before tick 222 (the first base group hit has no counterpart; entity 14 dies at t209 in fix, t329 in base).

## The five two-attacker hits (all in the base run)
| tick | subject | attackers | shares | outcome |
|---|---|---|---|---|
| 222 | 36 (raider) | 14, 16 | 13, 13 | SURVIVE |
| 226 | 36 | 14, 16 | 13, 13 | SURVIVE |
| 230 | 36 | 14, 16 | 13, 13 | SURVIVE |
| 1573 | 30 | 3, 11 | 4, 4 | SURVIVE |
| 1575 | 30 | 3, 11 | 4, 5 | SURVIVE |

The base tree has no new fields, so the felt swing "after" was computed offline from the recorded shares and the recorded engaged sets over the 12 ticks after each hit (alive assumed for engaged). The new rule differs from the old on 1, 5, 9, 8 and 8 of the 12 rows, and flips lethal vs not-lethal on none. Example, t230 hit, t234: subject 36 hp 5, both attackers engaged: old 13, new 26, both lethal. t1579: only attacker 11 engaged: old 0, new 4 (hp 103), not lethal. No hold starts or ends because of these hits: the base run's only holds are entity 14 at t323 and t325, which is not a subject of the five.

The fix run has one such hit: t435, subject 35 (raider), attackers 7 and 10, shares 6 and 8, hp 15 before. Old rule: swing 0 from t436 (the first attacker 7 is not engaged), no hold. New rule: swing 8 (attacker 10 engaged) at hp 0-1, lethal. A hold STARTS: held t437-442 (6 ticks), and the subject dies COMBAT at t455. The hold did not save it.

## Holds and deaths, base vs fix
| | held ticks | runs | total length | longest | no-hit holds of 50+ | in force at last tick | deaths |
|---|---|---|---|---|---|---|---|
| base | 2 | 2 | 2 | 1 | 0 | none | 30 (26 COMBAT, 4 HAZARD) |
| fix | 37 | 4 | 37 | 29 | 0 | none | 29 (24 COMBAT, 4 HAZARD, 1 DEFEAT) |

Fix holds by entity: 35 (t437-442, the group hit above), 4 (t915 only; dies COMBAT t916), 6 (t1437, then t1542-1570; survives to a HAZARD death at t1945). Entities 4 and 6 follow single-attacker hits, so the old rule would also hold there: they come from the diverged trajectory, not from the shares. Deaths only in base: 10, 5, 8, 9; only in fix: 11, 3, 6.

STOP rules (rpg-planner-ubuntu, from the designer's ruling): no fix-only no-hit hold of 50+ ticks, no fix-only hold in force at the last tick. Neither fires.

## Honest limits
- The cell ran both tickets together. The divergence before t222 cannot come from a group hit (neither run has one before t222), so it most likely comes from ticket 2's term (any entity hit by one attacker can now change its target) or from the act-test change on other paths. The cell does not separate them, and I did not try.
- One seed, one world, 2000 ticks. The holds that differ in the fix run are mostly the diverged trajectory, which this cell cannot separate from the effect of the shares.
- Peak memory is the scope's MemoryPeak sampled every 5 s.
- Hot-loop timing is NOT MEASURED (perf pause #715 6556861718). The wall times above are not a timing claim.
