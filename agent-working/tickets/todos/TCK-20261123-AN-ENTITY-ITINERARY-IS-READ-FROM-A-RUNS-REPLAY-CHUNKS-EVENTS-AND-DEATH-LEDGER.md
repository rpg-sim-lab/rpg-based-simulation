---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261123-AN-ENTITY-ITINERARY-IS-READ-FROM-A-RUNS-REPLAY-CHUNKS-EVENTS-AND-DEATH-LEDGER
phase: open
date: 2026-11-23
tags: []
---

# TCK-20261123-AN-ENTITY-ITINERARY-IS-READ-FROM-A-RUNS-REPLAY-CHUNKS-EVENTS-AND-DEATH-LEDGER

## Title
An entity's itinerary (its key moments) and its full route (every tick) are read from a finished run's replay chunks, events and death ledger

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
OWNER DIRECTION, #715 7094402354. The owner's words: "A tool that reads the replay files, looking good, but if you can build a route tracking (every moment) it would be good, you can decide between the complex and simple information, either easy to implement".

Routing: re-routed to rpg-planner as RPG observability (#715 7095232561; the ubuntu routing was withdrawn in 7095238616). rpg-designer confirms the shape (relayed by lead-planner-u24).

The lead's survey at dc379344b, as the lead labelled it ([code] = read in the code, [inf] = inference):
- The default LIGHT event files have no arrival, work, eat, rest, flee, lodging or project events [code].
- The replay chunk_*.json files are on by default (kernel.py:644-655, 365-378) [code].
  - They hold each tick's per-entity update: new_position, target_set, path_set, lodged_in_set, movement_mode_set and property_updates (core/updates.py:77-94, 200) [code].
  - No reader exists [code].
- Building ids are 20000+ in spec order (worldbuilding/compiler.py:660-686) [code]. Their names and positions need a 0-tick compile from the manifest's seed and world [code + inf].
- The replay buffer can drop its oldest entries (replay_manager.py:48-53), and the governor can turn replay off (kernel.py:220, 552) [code].

rpg-planner inspected at cdb0d4f09:
- `src/cli/entry.py:46-49`: the `inspect` subparser takes --id/--seed/--ticks.
- `src/cli/entry.py:939-940`: the handler only prints "V2 Inspect mode not yet fully implemented...".
- No test under tests/ references this stub; the `inspect` hits in tests/cli are the world and lab CLIs.

## Scope
1. A read-only reader, `src/observability/reporting/entity_itinerary.py`. It makes one pass over a run dir's replay chunks, simulation events and death ledger for one entity id.
2. Default output, the itinerary: key moments only, with building names and kinds from a 0-tick compile. Example: "t310 heads to Work Hall#20003 (12,4) → t360 arrives → … → t1200 dies (STARVATION)". The moments are:
   - a target change;
   - an arrival on a building's service tiles;
   - a lodging change;
   - a movement-mode change (flee, hold);
   - a gold change;
   - combat start and end (from simulation_events);
   - death (death ledger).
3. `--full`, the route: every tick's (tick, x, y, target, mode, lodged_in), written as JSONL or CSV.
4. Gap check: the reader checks that the chunk ticks are continuous and prints every gap (a dropped buffer, or replay turned off). It never fills in a missing tick.
5. CLI: the `inspect` stub in src/cli/entry.py becomes `inspect --run <dir> --entity <id> [--full] [--format jsonl|csv]`. The stub's old --id/--seed/--ticks flags and its print line go.
6. The output is a shaped read model (typed records), not raw domain objects.
7. Target naming (a finding by agent-working-designer via the leads; lead-planner-u24 verified updates.py:64 `target_set: Optional[tuple[float, float]]`). Targets are COORDINATES, not building ids.
   - "heads to <building>" comes from matching the target tile against the compiled buildings' tiles or service tiles (service_reach.py:22: the building tile plus its 4 neighbours).
   - The strategic objective's target (a building id string), if present in the update, is a second source.
   - A target that matches no building is reported as a bare position.

## Out of Scope
- Any change to what a run records (event richness, replay policy, the kernel).
- Running a simulation. The 0-tick compile is not a run.
- Drawing the route (a later consumer of the --full output).

## Acceptance Criteria
1. On a small fixture run, the itinerary lists the expected moments in tick order, with building names.
2. `--full` emits one row per recorded tick, and its fields match the chunk updates.
3. A fixture chunk with a deliberate tick gap makes the reader report that gap. The rows on either side are intact and nothing is invented.
4. A missing death-ledger or events file degrades with a stated note; it never crashes.
5. An architecture test shows that reading does not change the run dir.
6. The docs are updated: an observability doc names the tool, its inputs and its gap rule.
7. A target on a building's service tile is named with that building; a target on no building prints as a bare (x, y).
8. A run whose chunks lack a field (for example lodged_in_*) reports that field as UNKNOWN and lists the missing fields; it never reads a missing key as "not lodged".

## Related Tickets
- TCK-20261020-INSPECT-PANEL-READS-A-STATE-SELECTED-SHAPE-THE-BACKEND-DOES-NOT-SERVE (a different "inspect", the frontend panel; checked, not a duplicate)

## Related Docs
- docs/observability/ (the home of the tool's doc); docs/engine/kernel.md (the persistence phase)

## Related Stored Artifacts
- #715 7094402354, 7095232561, 7095238616

## Related Code Areas
- src/observability/reporting/ (history_query.py, run_report.py, run_determinism.py); src/cli/entry.py; src/core/updates.py; src/engine/kernel.py; src/worldbuilding/compiler.py; the replay manager

## Assumptions / Open Questions
- Sample run dirs come from lead-planner-u24 on request. The test fixture is built small and committed under tests/, not copied from data/runs.
- The --full output path is a CLI argument and defaults to stdout. Nothing is written into the run dir.
- Order: the rpg backlog, behind #995 and #996. It needs no host slot for a run, but its tests need a host gap.

## Durable state, lifecycle and clocks
None. The tool is read-only, and its output is ephemeral.

## Implementation Notes
Chunk-shape leads, to CONFIRM at investigation. They are from agent-working-designer's local check, relayed by the leads, and NOT verified by either lead:
- A chunk is a list of REFINED_UPDATE events. payload.update.entity_updates is keyed by the entity id as a STRING.
- navigation.target_set is [x, y]. updates.py:64 types it Optional[tuple[float, float]] (verified by lead-planner-u24).
- Older chunks have no lodged_in_* keys at all. A missing key means UNKNOWN, never "not lodged", so the tool prints which fields a run's chunks lack.

## Test Summary

## Files Changed

## Completion Summary
