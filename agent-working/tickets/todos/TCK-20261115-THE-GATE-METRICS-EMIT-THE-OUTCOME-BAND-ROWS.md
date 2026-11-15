---
status: active
layer: observability
authority: P1
audience: agent
ticket_id: TCK-20261115-THE-GATE-METRICS-EMIT-THE-OUTCOME-BAND-ROWS
phase: open
date: 2026-11-15
tags: []
---

# TCK-20261115-THE-GATE-METRICS-EMIT-THE-OUTCOME-BAND-ROWS

## Title
The RPG gate metrics emit the outcome-band rows (B1, B2, B3, B4): a starving-line flag, a typed meal-source record that includes the free core relief, and the people alive share at checkpoints

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
The owner decided on report-only outcome bands (#715 6892728142, direction 6892558147). rpg-designer set the levels and values from the fiction (#634 6892753019). testing-planner filed the testing half, TCK-20261115-THE-GATE-REPORTS-WHETHER-EACH-WORLDS-OUTCOMES-STAY-IN-THEIR-BANDS (0fd1a3aca): the config, the band shards, the judgement and the report section. This ticket covers the producers, which are rpg-owned: src/observability/rpg_gate_metrics.py and any typed src record they read. Filing only. The build is its own owner ask (6892728142: "the build comes back to the owner as its own ask").

## Scope
1. **B1 producer:** a per-seed flag `O1.seeds_reaching_starving_line`, true when at least one person's hunger reaches 95. Read from typed hunger state at the biological cadence. Also print, with no band, starvation deaths by kind and the first tick a person reaches the line.
2. **B2 producer:** a typed meal-source record per person and per source:
   - CARRIED_FOOD (with origin: foraged means origin NODE);
   - CORPSE_FOOD (corpse_killer_unknown, accepted);
   - TOWN_SERVICE (paid, gold > 0);
   - the free core EAT relief: a -40 hunger on the subject's own update with no transfer, which O4.accepted can't see (the D73 blind spot).
   - It comes from a typed record or event, never a reason string, and a meal counts only if the subject's stored hunger fell that tick.
   - Lane C's meal-source tally classes (the read-only spy under owner 6892576553) are the model.
   - Animals are reported by source, with no band.
3. **B4a producer:** the people alive share (alive / people ever alive; people = the D43 trade-trait flag) at every 500-tick checkpoint and at the last tick.
4. **Rows, emitted with the ids and groups the testing config names:**
   - pooled: B1, B2b, B3a, B3b, B4b;
   - run-level: B2a, B4a.
   - B3b's pooled death count is emitted as its own field, so the judged-only-when-10-or-more rule reads it directly.
5. **Interface, agreed with testing-planner on 2026-11-15.** Every row has the shape {id, class: "outcome", scope, world, group, value, band: true}. Band rows carry no `k` or `floor`, and `band: true` keeps them out of the change gate's drift and validity judgement, so the candidate and baseline row set doesn't change.

   | band | id | scope | group | value |
   |---|---|---|---|---|
   | B1 | `O1.seeds_reaching_starving_line` | pooled | people | int; print-only fields `starvation_deaths_by_kind` and `first_starving_tick` |
   | B2a | `O4.meal_sources_with_a_meal` | run | people | int |
   | B2b | `O4.meal_source_max_share` | pooled | people | float; `by_source` {CARRIED_FOOD, CORPSE_FOOD, TOWN_SERVICE, FREE_CORE_RELIEF} |
   | B3a | `O2.seeds_with_combat_death` | pooled | all | int (COMBAT or DEFEAT) |
   | B3b | `O2.max_cause_share` | pooled | all | float; `pooled_deaths` (int) and `by_cause` |
   | B4a | `O2.people_alive_share_min` | run | people | float; `by_checkpoint` |
   | B4b | `O2.seeds_people_all_alive` | pooled | people | int |
   | (none) | `O4.meal_sources_animals` | run | animals | unbanded |

   - **Pooling is done by this module,** like O2.seeds_with_survivors. The harness calls the pool function twice: once on 42-46, the change gate, and once on 42-51, which produces a separately named pooled band document.
   - The pool function takes whatever seed list the documents carry and never assumes 5 seeds.
   - Run-level rows, and the per-seed parts that pooled rows need, come from each seed's document.

## Out of Scope
- The band config, the judgement and the report section (the testing ticket).
- B5, coin flow (deferred by the owner).
- Any change to behaviour.

## Acceptance Criteria
- Each producer reads typed state or records only. Tests cover each one, including a free-relief meal that O4 can't see.
- Behaviour-neutral: a hash-equal run on the gate worlds against main. If a new typed record joins the event stream, state whether the event stream moves.
- The parity ledger (infrastructure.yaml) and the observability doc are updated in the same change.

## Related Tickets
- TCK-20261115-THE-GATE-REPORTS-WHETHER-EACH-WORLDS-OUTCOMES-STAY-IN-THEIR-BANDS (testing; depends on this one)
- TCK-20261007-NOBODY-EATS-OR-SLEEPS-AND-EVERY-ENTITY-STARVES-BY-TICK-1100 (closed; its re-run gives the meal-source model)
- PR #781 (decision 73, the paid inn meal) and the free-relief blind spot

## Related Docs
- docs/mechanics/01_entity_anatomy.md ("Staged Starvation")
- docs/world_rules/life-body/survival-needs.md
- docs/observability/

## Related Stored Artifacts
None.

## Related Code Areas
- src/observability/rpg_gate_metrics.py
- src/engine/domain/core_actions.py (eat_update, :123)
- src/engine/building_services.py (service_delta, :92)
- src/systems/resource_transactions (resolver)

## Assumptions / Open Questions
- Is a typed meal event emitted at apply time, or is the source derived from the committed update? Decide at scoping. The choice decides whether the event stream moves.
- The measurement tier is stated at dispatch. An observability change needs a hash-equal proof only.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
