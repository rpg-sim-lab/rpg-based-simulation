---
status: active
layer: combat
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261115-PAST-THE-STARVING-LINE-THE-TACTICAL-STEP-TURNS-AWAY-FROM-A-MEAL-WITHOUT-WEIGHING-HUNGER
phase: open
date: 2026-11-15
tags: []
---

# Investigation: a swing left behind turns a starving subject away from its meal

Source of truth: rpg-designer's FINAL design v1 (main checkout `.claude/handover/drafts/rpg-designer-d1-starving-tactical-design.md`, sha256 starts e7f326dcc6f6), owner #715 6894693356 (dispatch) and 6893303548 (design choice), step 0 (#715 6893555631; spy f349e5fd on tree 824483949; `/mnt/data2/rpg-measure/d1step0/a.json` sha 15fb056c..., `b.json` sha 4889b9d4..., both REPRO_OK, ERRORS 0, PINNED). Code read on origin/main f94417e6f.

## The predicate and its callers (origin/main)
- `src/engine/tactical_threat.py`: `_hit_acts_on(hostile, subject, tick)` is `subject.combat.last_hit_tick is not None and last_attacker_id == hostile.id and tick - last_hit_tick <= NEED_WAKE_CADENCE` (10). No reach test: wherever the hitter now is, it "acts" for 10 ticks. `hostile_acts_on` = `_task_acts_on` (term a) or `_hit_acts_on` (term b). `need_yields` = any hostile acts.
- Callers of the pair, all through `hostile_acts_on` / `need_yields`: `tactical._panic_holds` (past the consequence line a panic stands only if a threat acts), `tactical._need_path_first` (via `need_yields`: the need runs first unless a hostile acts), `present_threat.acting_threat_to` (goal level: `scorers.py` lines 66 and 245), and `_panic_yields_to_need` (through `_need_path_first`).
- Lines: `STARVING_LINE` = 95.0 in `src/engine/starvation.py` (the table, no imports beyond dataclasses); `need_pull.HUNGER_LINE` is also 95.0; `_panic_holds` tests `hunger >= HUNGER_LINE or sleep_debt >= SLEEP_LINE`.

## What step 0 showed (designer's recount of the raw rows)
- A (crowded s45, e5, t2155): hp 1%, hunger 100, inn 2 ticks off. `_panic_holds` True because e34 (distance 5, task None) acts through the HIT term only (it hit at t2151, the free swing e5's own step provoked). FLIGHT:PANIC_RETREAT away from the inn; e5 starves 6 ticks later.
- B (crowded s46, e4, t3226): hp 30%, hunger 100, inn 1 tick off. `need_yields` True because e36 (distance 2, task None) acts through the HIT term only (hit at t3216, exactly 10 ticks earlier). The engagement list then sorts e35 first (distance 8, not acting) and pursues it, away from the inn; e4 starves 2 ticks from the inn.
- The hp < 15% branch: 0 attack returns below 15% in either window (7 + 1). Parked by the designer, not folded in.

## The fix (designer v1, no new number)
Past the starving line only (subject hunger >= STARVING_LINE): a hit counts as acting only while its hitter can still reach the subject, Manhattan <= max(1, hostile.combat.range); term (a) is unchanged; below the line the 10-tick window is unchanged. One place: `_hit_acts_on`, so `need_yields`, `_panic_holds` and `acting_threat_to` all get the same predicate.
Not in this fix: narrowing the engagement list to acting hostiles after a need yields (B's ordering is the group shared-target bias, ubuntu's TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET); the hp<15% branch order.

## Facts the plan relies on (to verify in the build, not assumed)
- `hostile.combat.range` exists on CombatComponent and is the attack reach in tiles (it is read as `h.combat.range > 2` for ranged threats in tactical.py).
- Positions are floats; Manhattan distance is the metric the file already uses (`_distance`, ADJACENT_DISTANCE = 1.0).
- `acting_threat_to` calls `need_yields` over `perceived_hostiles`, so it needs no change of its own.
