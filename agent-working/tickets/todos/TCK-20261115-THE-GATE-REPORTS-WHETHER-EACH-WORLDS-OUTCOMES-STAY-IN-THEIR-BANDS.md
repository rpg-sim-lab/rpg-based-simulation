---
status: active
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261115-THE-GATE-REPORTS-WHETHER-EACH-WORLDS-OUTCOMES-STAY-IN-THEIR-BANDS
phase: open
date: 2026-11-15
tags: [testing, simulation-quality]
---

# TCK-20261115-THE-GATE-REPORTS-WHETHER-EACH-WORLDS-OUTCOMES-STAY-IN-THEIR-BANDS

## Title
The RPG gate reports, in its own report-only Bands section, whether each world's outcomes over 10 seeds stay inside the fiction's bands

## Status
OPEN (filed. The BUILD is its own owner ask via lead-planner-u24, not yet asked. It is also blocked on rpg's producer ticket, see Related Tickets)

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
- Owner decision #715 6892728142: bands B1 to B4 go in the regression gate, in their own report-only Bands section. They are absolute per world, use 10 seeds (42-46 unchanged, plus a 47-51 band set in the same run), and never block until the owner says. The cost is measured before the shape is fixed.
- Placement is testing-planner's #634 6892721694. The levels and values are rpg-designer's #634 6892753019, set from the fiction before any band rows exist (decision 33).
- B5 (coin flow) is deferred.
- This ticket is the testing half: the band judgement and the band seed set. The rows' producers live in rpg's metric module and in typed src records, and are rpg's ticket.

## Scope
1. **Thresholds.** Add a `bands:` block to `tests/simulation_quality/rpg_gate/config.yaml`, beside `stop_lines:`. Each entry has:
   - `name`, `metric` (with `group` where a row has one) and `level` (`run` | `pooled`);
   - `[min, max]` per world, with a missing world meaning no band there;
   - a judged-only-when condition where rpg-designer gave one (B3b: pooled deaths ≥ 10, else printed "too few");
   - the fiction `reason`, copied from 6892753019.
   - The rows are B1, B2a, B2b, B3a, B3b, B4a and B4b. Rows printed with no band (starvation deaths by kind, the first starving tick, the free-relief and TOWN_SERVICE shares, animal sources) are listed under `print_only:` in the same block.
   - The config loader (`rpg_gate_baseline.load_config`, `GateConfig`) validates the block. It refuses an unknown level, a min greater than max, or a world not in `worlds`.
2. **Band seed set.** `config.yaml` gains `band_seeds: [47, 48, 49, 50, 51]`.
   - The plan (`rpg_gate_plan`) emits one band shard per world beside today's shards, so no shard grows past today's size. The shard job's timeout-minutes is 120, and 5 seeds already fill it.
   - Band shards run the same harness with the same pinned settings, ticks, `harness_hash` and PINNED runner check. Their documents are named so they never mix into the change gate's documents.
   - The change gate (drift, validity, known-reds, baseline candidate) reads only `seeds` (42-46), exactly as now.
3. **Band judgement**, in `tools/test_architecture/rpg_gate_report.py` (or a new `rpg_gate_bands.py` it calls).
   - Pooled band rows pool all of `seeds` + `band_seeds` per world. Run-level band rows are judged on each of the 10 seeds.
   - Each band row is IN, OUT (below or above) or not judged ("too few", or a world with no band).
   - It is never a `fail`, `drift`, `unstable` or `no-data` finding, and it never changes the report's RED/GREEN verdict.
   - A band set with any NOT_PINNED or `no-data` document is reported as "band set incomplete", naming the documents. It is never judged on fewer seeds.
4. **Report and tracker.** A **Bands** section in the report markdown and JSON, per world and row: the value, the band, the seed count, IN/OUT, and the print-only rows beside it. The rolling tracker issue (#669, `rpg_gate_issue`) lists band OUTs in their own advisory list, separate from reds.
5. **Re-baseline.** A band OUT on the candidate's run means `rebaseline()` needs an owner ruling, as a crossed stop line does today. It never refuses on its own.
6. **Docs.** `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md` and the gate's report doc gain the Bands section and the `bands:` / `band_seeds:` config. Editing `config.yaml` moves `harness_hash`, so the baseline goes stale. That is intended, and the PR declares it.

## Out of Scope
- The producers: `O1.seeds_reaching_starving_line`, the typed meal-source record including the free core EAT relief, and the people-alive share at checkpoints. Those are rpg's ticket (src and metric module).
- Choosing or changing any band value. That is rpg-designer's, and a value moves after its row is seen only with an owner ruling.
- Making a band blocking. That would be a separate owner decision, and would then need a band state in known-reds.
- B5 coin flow.
- Changing the change gate's 5 seeds, SE or floors.

## Acceptance Criteria
1. For every band row, a positive and a negative test on synthetic documents: inside, below and above the band, and judged-only-when (B3b "too few"). A band that cannot trip fails its test.
2. Config validation tests: an unknown level, min > max, an unknown world and a missing reason are each refused.
3. The plan emits 3 band shards (one per world) on top of today's 3. A static test on `rpg-gate-report.yml` and the plan shows that shard size is unchanged and that band documents never enter the change gate's inputs. A change-gate report built from a docs dir that includes band documents is identical to one built without them.
4. "Band set incomplete" is reported, not judged, when a band document is NOT_PINNED or `no-data`.
5. The report's RED/GREEN verdict and its exit code are unchanged by any band result (tested).
6. Cost: ONE measured `workflow_dispatch` run of the gate with the band shards, on a branch, under the owner's build ask. It states per-shard wall time, total wall time and runner-minutes. The shape (band shards as separate jobs, or more workers per shard) is fixed only after that number is reported to the owner.
7. The existing rpg_gate tests (harness, report, candidate, baseline, plan, issue, known_reds, workflow shape) pass.

## Related Tickets
- rpg's producer ticket (to be filed by rpg-planner): B1 starving-line flag, B2 typed meal-source record including the free core EAT relief (the D73 blind spot), B4a people-alive share at checkpoints. This ticket's build depends on it.
- TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC (done): the gate it extends.

## Related Docs
- #715 6892558147 (owner direction), 6892728142 (owner decision)
- #634 6892584450 (rpg-designer proposal), 6892721694 (testing placement), 6892753019 (levels and values)
- docs/plans/test_architecture/reference/rpg_gate_baseline_format.md

## Related Stored Artifacts

## Related Code Areas
- tests/simulation_quality/rpg_gate/config.yaml
- tools/test_architecture/{rpg_gate_plan,rpg_gate_harness,rpg_gate_report,rpg_gate_baseline,rpg_gate_issue}.py
- .github/workflows/rpg-gate-report.yml

## Assumptions / Open Questions
- The band shards fit in the same workflow run: 3 more shard jobs, each at today's size. To be confirmed by AC6's measured run before the shape is fixed.
- The baseline is stale (the harness hash moved in a25619971), and bands do not depend on it. They can land before the next re-record.

## Implementation Notes
- **Row interface, agreed with rpg-planner on 2026-11-15** (its TCK-20261115-THE-GATE-METRICS-EMIT-THE-OUTCOME-BAND-ROWS Scope 5, seat-8 e8f6c6378).
  - Every band row is `{id, class: "outcome", scope, world, group, value, band: true}`, with NO `k` or `floor`.
  - The judge and report key ONLY on `band: true`. A `band: true` row is excluded from drift, validity, the baseline candidate and the row set, and a test pins that.
  - The rows:
    - B1 `O1.seeds_reaching_starving_line` (pooled, people; print-only fields `starvation_deaths_by_kind`, `first_starving_tick`);
    - B2a `O4.meal_sources_with_a_meal` (run, people);
    - B2b `O4.meal_source_max_share` (pooled, people; `by_source` with keys CARRIED_FOOD, CORPSE_FOOD, TOWN_SERVICE, FREE_CORE_RELIEF);
    - B3a `O2.seeds_with_combat_death` (pooled, all);
    - B3b `O2.max_cause_share` (pooled, all; `pooled_deaths` for the at-least-10 rule, plus `by_cause`);
    - B4a `O2.people_alive_share_min` (run, people; `by_checkpoint`);
    - B4b `O2.seeds_people_all_alive` (pooled, people);
    - `O4.meal_sources_animals` (run, unbanded, print-only).
- **Pooling is rpg's module, not the judge.** The harness calls the module's pool function twice: on `seeds` (42-46) for the change gate, unchanged, and on `seeds` + `band_seeds` (42-51), written to a separately named pooled band document. Pooled band rows are read only from that document. Run-level band rows come from each of the 10 seeds' documents.

## Test Summary

## Files Changed

## Completion Summary
