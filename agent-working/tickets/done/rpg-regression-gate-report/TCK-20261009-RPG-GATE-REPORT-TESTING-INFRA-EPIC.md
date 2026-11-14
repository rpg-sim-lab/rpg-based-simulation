---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC
phase: done
date: 2026-10-09
tags: [testing, regression, simulation-quality, planning]
---

# TCK-20261009-RPG-GATE-REPORT-TESTING-INFRA-EPIC

## Title
Testing-side infrastructure for the rpg regression gate report: harness, baselines, report states, ownership registry, scheduled workflow

## Status
DONE

## Tier
epic

## Type
feature

## Priority
P1

## Request Summary
The owner asked for durable regression control on rpg behaviour (2026-10-09). rpg-planner and rpg-designer defined the metric set v1 (`.claude/handover/drafts/rpg-regression-metric-set-v1.md` (rpg-planner + rpg-designer, 2026-10-09)): VALIDITY metrics V1-V7 (exact, can FAIL) and OUTCOME metrics O1-O7 (paired against a baseline over 5 seeds with k*SE plus a floor; a crossing is DRIFT, "trace the cause", never FAIL on its own). The agreed split (rpg-planner and testing-planner, 2026-10-09):
- **rpg**: metric definitions, oracles and Bible citations, k and floors, baseline content, the metric computation from typed records, the SimQ needs/livelihood validity pillar.
- **testing (this epic)**: the harness (a fresh process per world/seed, everything pinned), the baseline file format and staleness, the report states (pass / fail / drift / unstable / stale / no-data), the rerun-same-SHA step, the ownership registry (generalised from the slow-regression known reds) and the rolling issue, and the scheduled plus on-demand workflow (the #464 gate pattern; advisory first).

**Metric contract (shared by every child; rpg implements the computation, testing everything around it).** For each (world, seed) run, the rpg metric module turns that run's typed records into one JSON document:
```
{"schema": "rpg-gate-metrics/v1", "world": "...", "seed": 42, "ticks": 5000, "sha": "<commit>", "harness_hash": "<hash>",
 "metrics": [
   {"id": "V1", "class": "validity", "scope": "run",    "group": "*", "violations": 0, "examples": [ ... up to 5 ... ]},
   {"id": "V7", "class": "validity", "scope": "pooled", "group": "wolves", "counts": { ... raw, opaque to testing ... }},
   {"id": "O2.deaths", "class": "outcome", "scope": "run", "group": "guards", "key": "STARVATION", "tick": 5000, "value": 3}
 ]}
```
**Amendment (rpg-planner, 2026-10-09, accepted before child 3):**
- **`scope`**: every metric is `run` or `pooled`. A pooled validity metric (V7 "no dead way" and its hunt instance) is judged over all seeds of one world, not per run, so one seed without a hunt is not a violation. Per-run documents carry its raw `counts`. rpg's module also exports `pool(docs_for_one_world) -> [metric]`, which returns `{id, class: "validity", scope: "pooled", group, violations, examples}` for the world. The harness calls it after all seeds of a world finish and never interprets `counts`.
- **Outcome shape**: `value` is a number, with optional `key` (for example a death cause) and `tick` (a checkpoint). Pairing across seeds is by `(id, group, key, tick)`. The config's floor is keyed by `id` and applies to every key and tick of that id.
`class` is `validity` (exact or logical: `violations` is an integer, and any non-zero value is a FAIL) or `outcome` (`value` is a number; compared paired against the baseline; a crossing is DRIFT, never FAIL). `group` is a kind group or `*`. Metric ids, groups, oracles, k and the per-metric floors belong to rpg (the metric set v1: V1-V7, O1-O7). testing never hard-codes a metric id.

## Scope
Children, in order (see SEQUENCE.md):
1. TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE: the known-reds schema, matcher and lint move into a shared module; the slow report keeps identical behaviour; a second registry kind for metric ids.
2. TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS: the versioned, immutable baseline format, staleness, the dual reference (last plus milestone-first) and the re-baseline citation check.
3. TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS: the pinned, fresh-process harness that runs the matrix and collects metric JSON documents.
4. TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN: evaluation, report states, the same-SHA rerun that marks UNSTABLE, and JSON plus markdown output.
5. TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW: the scheduled daily job plus `workflow_dispatch` on a ref, the #464-style gate, the rolling issue, advisory only.

## Out of Scope
- Metric definitions, oracles, thresholds, baseline content, the metric computation module and the SimQ pillar scorer (rpg's tickets; rpg-planner cross-links them).
- Making the report a required check (principle 8: a recorded owner decision after the post-pilot review, based on the observed false-positive rate).
- Any authority role: the report cites the Bible and the parity ledger, and never becomes a proof-status record (roadmap principle 3).

## Acceptance Criteria
1. All five children closed.
2. One daily report on main, and one dispatched report on a branch, both produced end to end against a real baseline, with every state the run can reach visible in the summary (at least pass, plus one non-pass state from a seeded fixture in the tests).
3. A same-SHA rerun that disagrees produces UNSTABLE and routes to test infrastructure, not to the feature team.
4. Roadmap §4.1/§4.2 updated: a new broad-simulation evidence layer, "rpg gate report (system health; advisory)".

## Related Tickets
- rpg-side tickets (rpg-planner files them and cross-links): the metric computation module, the SimQ needs/livelihood validity pillar.
- TCK-20261009-SLOW-REGRESSION-OFF-HOUR-AND-SKIP-UNCHANGED-MAIN (#464 gate pattern reused)
- TCK-20261009-PINNED-NORMAL-GOVERNOR-SHARED-TEST-HELPER (the pin the harness uses)
- TCK-20261001-SIMQ-GRADE-ANCHORS-RED-ON-MAIN-UNREPORTED (the flapping single-run anchors the pillar replaces)

## Related Docs
- `docs/plans/test_architecture/roadmap.md` §3 (principles 1, 3, 4, 5, 8), §4.1, §4.2, §4.5
- `docs/brainstorm/simulation-rule-taxonomy-evaluation-direction.md` §5 (outcome neutrality)
- `docs/engine/deterministic_execution.md` (audit_mode and wall-clock inputs)
- the metric set v1 draft (see Request Summary)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/test_architecture/` (new modules)
- `tools/test_architecture/slow_known_reds.yaml`, `slow_regression_report.py` (generalised in child 1)
- `tests/helpers/kernel_pinning.py`
- `.github/workflows/` (a new workflow in child 5)

## Assumptions / Open Questions
- Cost: about 15-30 runs of 5000 ticks per report (rpg-planner's estimate). Child 3 measures it; child 5 sizes the CI matrix from that measurement.
- Process-global state leaks between tests in one process (the strict-xfail and CONFLICT-04 findings, 2026-10-09), so a fresh process per (world, seed) is required, not optional.
- Where the config and baselines live: proposed `tests/simulation_quality/rpg_gate/` (rpg-owned content, testing-owned schema). Child 2 confirms the path with rpg-planner.

## Open live proofs
Both were due on the first scheduled run after rpg's metric module (`src/observability/rpg_gate_metrics.py`, rpg-planner's ticket) merged. Both are now MET; see the Completion Summary.
- Child 5 (`TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW`) AC2: the rolling issue created or updated by a scheduled run and untouched by a dispatch.
- The full-run wall time for 3 worlds x 5 seeds.

## Implementation Notes
- V8 (item 7, TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK) landed 2026-10-19: "every entity added mid-run has a declared source". Required-validity guard in the report and candidate, a self-test that drives rpg's real recorders and `compute` (test_v8_fires.py), and a static spawn-site guard with an OFF ratchet (tests/architecture/test_spawn_sites_declare_source.py).

## Test Summary
No code in this close. The children's own test summaries hold the test evidence. The unstable-state rule is unit-tested in tests/unit/tools/test_rpg_gate_report.py::test_a_rerun_that_disagrees_marks_unstable_and_routes_to_test_infrastructure.

## Files Changed
- This ticket (disposition close); the folder moves to agent-working/tickets/done/rpg-regression-gate-report/.

## Completion Summary
Disposition close, owner approval on issue #715, comment 6875225978 (item 3, "Close 4 empty epics"). It was read on origin/main fc62c8557 on 2026-11-14. Nothing was dropped or moved.

**Children: all 7 DONE.**
| # | Ticket | Landed |
|---|---|---|
| 1 | TCK-20261009-KNOWN-REDS-REGISTRY-SHARED-MODULE | #502, 4cb385343 (2026-10-11) |
| 2 | TCK-20261009-RPG-GATE-BASELINE-FORMAT-AND-STALENESS | #502, 4cb385343 (2026-10-11) |
| 3 | TCK-20261009-RPG-GATE-PINNED-FRESH-PROCESS-HARNESS | #502, 4cb385343 (2026-10-11) |
| 4 | TCK-20261009-RPG-GATE-REPORT-STATES-AND-SAME-SHA-RERUN | #502, 4cb385343 (2026-10-11) |
| 5 | TCK-20261009-RPG-GATE-SCHEDULED-AND-DISPATCH-WORKFLOW | workflow in #507, f8b558de0 (2026-10-11); ticket closed in #531, 9a9955f0d (2026-10-14), with AC2 open by its own allowance |
| 6 | TCK-20261011-RPG-GATE-BASELINE-CANDIDATE-FROM-HARNESS-DOCS | #508, f40ccadff (2026-10-11) |
| 7 | TCK-20261013-RPG-GATE-V8-SPAWN-SOURCE-CHECK | #653, 7f115a3d4 (2026-10-19); in done/ under its own id, AC1-AC7 all checked |

**Epic acceptance criteria.**
- AC1 MET: all children are closed, including items 6 and 7, which were added after the original five.
- AC2 MET. Daily report on main: scheduled runs from 2026-10-19 on run the full matrix (e.g. 43432156849 on 96db1f5e8, 2026-11-13). Dispatched report on a branch, end to end: 40734781335 (ref rpg-free-meal-own-step, 2026-10-28). Plan, all three shards, Evaluate (with rerun), the baseline candidate and the report upload succeeded, and the verdict was red, a real non-pass state. The seeded non-pass fixtures are in the children's tests.
- AC3 MET by unit test (see Test Summary). The finding routes to `test-infrastructure`.
- AC4 MET: docs/plans/test_architecture/roadmap.md lists the "Broad simulation: rpg gate report (advisory)" layer (line 109) and its states (line 127).

**Open live proofs, now closed.**
- Child 5 AC2, the rolling issue: #669 was created by github-actions on 2026-10-19 and updated (comment plus title rename) only at scheduled-run times, 12 times between 2026-10-20 and 2026-11-12. The branch dispatch 40734781335 skipped "Update the rolling issue", and no comment falls at any dispatch time. MET.
- Full-run wall time, 3 worlds x 5 seeds (run 43432156849): shards 13 / 18 / 37 min in parallel (urban_political / crowded_frontier / frontier_living_world), report job 71 min including the bounded rerun, 1 h 49 min end to end.

**Not part of this close.** The gate has been red on main since 2026-11-12 (runs 43231426067 and 43432156849: NEW V3 crowded_frontier/45 and /46). That is ownership work in tools/test_architecture/rpg_gate_known.yaml and rpg-planner's triage, not epic scope. Reported to lead-planner-u24 separately.
