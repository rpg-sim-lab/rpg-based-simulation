---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT
phase: inprogress
date: 2026-10-31
tags: []
---

# Plan: a COMBAT_RETREAT project completes when its threat is gone

Status: DRAFT for rpg-planner review. No code until approved. Base `6fdfdf555`; branch `rpg-retreat-completes`.

## 1. The completion fact
A COMBAT_RETREAT project's active objective ends (RESOLVED) and the project COMPLETES, `ended_by` THREAT_CLEARED, when **no present threat acts on the subject**:
`not any(distance(subject, h) <= ADJACENT_DISTANCE for h in hostiles) and not any(hostile_acts_on(h, subject, state.tick) for h in hostiles)`, with `hostiles = perceived_hostiles(subject, state)` (the subject's own perception: neighbour view radius 10, saliency cap 5, catalog hostility). `ADJACENT_DISTANCE` (= 1.0, orthogonal melee reach, decision 32) and `hostile_acts_on` (= `acting_threat_to`'s own test: the hostile's task attacks/pursues the subject, or it took hp from the subject within `NEED_WAKE_CADENCE` ticks) are the same definitions the pull uses. One new pure helper `retreat_threat_present(entity, state)` in `src/ai/goals/present_threat.py` (next to `acting_threat_to`; a pure read), so the pull and the end cannot drift.

**Which tick's state it reads.** `state` is the authoritative snapshot passed into `StrategicIntelligenceSystem.evaluate_strategic_intent` and into `StrategicWorkQueue.build` in the same strategic phase of tick T; both read it, so `state.tick` = T and the evaluator and the queue see the same perception, positions and hit history (state at the start of the phase, before this tick's intents are applied). A threat that appears in tick T's intents is seen at T+1. Latency from threat-gone to end = the first strategic evaluation after it (the queue puts it in tier 3 on the same tick, so it is bounded by the strategic budget, not by the 20-tick goal-selection cadence); a unit test pins "ends in the first evaluation after the threat leaves".

**Where.** A retreat branch in `objective_outcome` (`entity_target_objective.py`), guarded first by `project.kind == GoalKind.COMBAT_RETREAT` (cheap; `perceived_hostiles` runs only for retreat holders). The evaluator reaches it through the existing `close_entity_target_project` call and the work queue through its existing `objective_outcome(...) is not None` test, so both agree by construction. `objective_outcome` returns `(ObjectiveStatus, ProjectStatus)` today; it must also carry the end value, so its return becomes a small typed result (objective status, project status, `ProjectEnd | None`) with the existing callers adapted (2 call sites + `close_entity_target_project`). Entity-target and contract branches return `None` for the end (unchanged records).

## 2. Typed end (general, shared with lane B F3)
- `src/core/strategic.py`: add `THREAT_CLEARED` to `ProjectEnd`; keep `SUPERSEDED_BY_TARGET` and its ABANDONED pairing unchanged. Rewrite the docstring: `ended_by` is set once with the terminal status and never rewritten; each value names the status it pairs with (SUPERSEDED_BY_TARGET with ABANDONED, THREAT_CLEARED with COMPLETED). Lane B adds "way closed" the same way.
- One general writer helper `end_record(project, status, ended_by)` (replaces the body of the private writer; `supersede_record` becomes a thin call `end_record(p, ABANDONED, SUPERSEDED_BY_TARGET)`), and `close_entity_target_project` uses it when the outcome carries an end. It refuses to overwrite a set `ended_by`.
- **Readers of `ended_by` today:** the canonical-dict entry (`strategic.py` ~344-348, emitted only when set, so every project not ended this way keeps its hash), and `cognition_export.py:73` (copies `ended_by.value` into the exported attributes). No other reader (grep `ended_by|ProjectEnd` in `src`). What each does with THREAT_CLEARED: the canonical entry emits it (hash of a completed retreat changes, by design, only in runs that complete one); the export copies it. A test pins both.
- Status: COMPLETED + THREAT_CLEARED (designer: "completes").

## 3. Does anything treat a COMPLETED retreat specially?
Checked: `process_project_outcome` (turning point "victory"/"great_victory", boredom -2.0 for the kind) has **no caller in `src`** (grep); the closing path used by `close_entity_target_project` emits no turning point and no boredom change, and the new branch uses the same path, so a completed retreat earns no XP, reward, memory or boredom change (same as every other objective closed there). Consumers of COMPLETED status: `is_live_project`/`has_project_capacity` (COMPLETED is not live, which frees the slot: the point), `StrategicWorkQueue` tier 3 (a COMPLETED current project is evaluated, the entity re-decides), `building_arrival`/`work_queue`/`guild_visit` (unrelated kinds). Nothing else reads it. If review wants a "retreat survived" memory/turning point, that is a separate decision (it would add a no-caller function to the live path).
After the end the evaluator returns `current_project_id_set=""`, `current_objective_id_set=""`, as the entity-target close does; the next selection is the ordinary re-decision.

## 4. Flapping counter
A pure read-only observability counter (no state): at completion, record `(entity, end tick)`; at the next retreat adoption by the same entity, if `adopt_tick - end_tick <= FLAP_WINDOW` selection calls (= 3 calls, i.e. 60 ticks at the 20-tick cadence; named constant, reported not gated), increment `retreat_reentry_within_window`. Lives in the probe/measurement tooling (probe8 over the existing `pj`/`rh` records: an end is a `pj` change away from a retreat id with the prior id's status COMPLETED + THREAT_CLEARED), not in src, so no new durable state. Reported in the AC1 re-run next to N=50/200/1000. Risk to watch: 9 of the baseline's N=50 projects had never seen an acting threat while held (adopted from low hp / `is_fleeing` with no acting hostile). Those complete at the first evaluation after adoption and the scorer can re-propose them; no hysteresis in v1 per the ruling, the counter says whether that matters.

## 5. Files
- `src/systems/strategic_systems/entity_target_objective.py` (retreat branch; typed outcome)
- `src/core/strategic.py` (`ProjectEnd.THREAT_CLEARED`, `end_record`, docstring)
- `src/ai/goals/present_threat.py` (`retreat_threat_present`)
- `src/systems/strategic_systems/work_queue.py` and `intelligence.py` only to adapt to the typed outcome's shape (no logic change)
- `src/systems/strategic_systems/cognition_export.py`: no change expected; a test covers it
- Docs: `docs/mechanics/04_strategic_cognition.md` + `docs/engine/contracts/tactical_contract.md` section 4 (law), parity ledger row (`docs/parity_ledger/strategic_cognition.yaml`), `docs/guidelines/intentional_divergences.md` (Enforced), `registries/mechanisms.yaml` only through rpg-planner.
- NOT touched: `src/core/state.py`, `src/engine/apply_plan.py`, the group store, the capacity gate (`intelligence.py:1768`), the :1610 lookup rules.
- Import check: `src.systems.strategic_systems` already imports `src.ai.goals.*` (intelligence.py:87-90); the new edge `entity_target_objective -> src.ai.goals.present_threat` is the same layer pair; verify with `import_contracts ci` before any push (lesson from #779), and a fresh baseline line is NOT acceptable without codebase-planner.

## 6. Order of work
1. Tests first (test_plan.md items 1-8). 2. Helper + typed end + branch. 3. Scoped suites + codebase.health + import_contracts + completeness pins + perf inventories in-sync (the kernel/strategic code moves line numbers in `wall_clock_inventory`). 4. Gate-world hashes vs main (AC3: equal, or first diff is a THREAT_CLEARED end). 5. Docs/ledger/divergence. 6. Heavy slot for the 3x5x2000t re-run + s42 at 500/1000/2000t (AC1, AC6), ask rpg-planner for it. 7. Close per CLAUDE.md. Pushing needs an owner go via rpg-planner/lead.

## 7. Open points for review
1. `objective_outcome`'s return becoming a typed result touches `work_queue.py`/`intelligence.py` call shapes (mechanical). Alternative: keep the tuple and let the retreat branch live in a sibling `retreat_outcome` called from the same two places; slightly more code, smaller diff to the shared predicate.
2. Using `GoalKind.COMBAT_RETREAT` as the project kind guard (the project's `kind` is the GoalKind for goal-created projects, as the probe shows `proj_combat_retreat_<t>`).
3. A retreat adopted with no acting hostile (low hp / fleeing emotion) ends at once; accepted per the ruling, measured by the flapping counter.
