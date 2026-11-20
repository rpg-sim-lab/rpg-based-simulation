---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK
phase: done
artifact_type: investigation
date: 2026-11-17
tags: []
---

# Investigation: TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK (N10)

Rule source: `rpg_designer_ruling_2026-11-16.md` (v1.1) in this folder; the first scoping read (ubuntu) is in the ticket. This is the read of the merged tree (efba7d95c, then 9d13a3356) done by rpg-implementer-3.

## Every SUSPENDED writer (file:line on the merged tree)
- `evaluate_project_switch`, `src/systems/strategic_systems/intelligence.py` ~L1130 (replaced the current project with `replace(current, status=SUSPENDED)`).
- `_suspend_project_for_threat`, `src/engine/tactical.py` ~L172 (the threat suspend; sets the current ids to "").
- near-death, `src/systems/world_systems/events.py` ~L162 (no production caller; it left `current_project_id_set=None`, i.e. "unchanged", so the id stayed on a SUSPENDED record).
No other writer.

## Resume paths
`resume_project` (intelligence.py ~L1142) is the only writer of ACTIVE from SUSPENDED. Two production callers: the detour-completion block (~L1338) and `route_live_record` (src/ai/goals/live_record_route.py, divergence 2.143) at ~L1612. One clear in `resume_project` covers both.

## Where the expiry pass must run
`evaluate_strategic_intent` has early returns (dead/inactive, frozen, the harvesting fast-path, the objective-resolve return, the detour block) before goal selection; the pass must run before them, in the caller, so the freed slot counts on the same call. Production caller: `fused_strategic_pass` (~L619). `evaluate_all_strategic_intents` has no production caller (filed as TCK-20261117-EVALUATE-ALL-STRATEGIC-INTENTS-IS-DEAD-CODE-THAT-SKIPS-THE-SUSPENSION-EXPIRY).

## Cadence
`SystemCadence.strategic_intelligence` is 10 by default; the gate worlds run `PROD_SMALL` = 20 (`src/config/profiles.py`, `tools/test_architecture/rpg_gate_run.py`). A SUSPENDED record is therefore expired 200 to 209 ticks (default) or 200 to 219 ticks (gate profile) after it was suspended: visible bound TTL + cadence - 1.

## Checkpoint / hash touch points
`ProjectState` (src/core/strategic.py) gets `suspended_since`, appended last and omitted from the canonical dict while None (`canonical_extra`); `FIELD_RULES` row in `src/engine/checkpoint_fields.py`; cognition export shows it.

## Evidence for the leak
Lane D's urban_political corpus runs (50-75% of survivors at the cap with 1-3 SUSPENDED records from t~550, never falling; script /tmp/claude-1000/capread.py); the 10-31 and 11-02 counts in the ticket.
