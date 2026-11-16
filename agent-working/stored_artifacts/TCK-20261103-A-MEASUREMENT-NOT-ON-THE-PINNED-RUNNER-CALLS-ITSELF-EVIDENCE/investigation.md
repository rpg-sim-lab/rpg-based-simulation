---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE
phase: done
date: 2026-11-15
tags: [testing, determinism, observability]
---

# TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE: investigation

## Evidence run (rpg-planner HOST FREE, 2026-11-15 21:27:30Z to 21:33:21Z, one process at a time, no commit during it)
Tree: testing-pinned-evidence-and-m1-probes @ 967ab45af3abd930d2c4a365ff48d1032c1b7702 (clean). Main side: `git archive` of origin/main 5ba65854c02ec9d132adb985a30b945fa8525d29. Seed 42, 1000 ticks, `rpg_gate_run.build_kernel`, end tick 1000, `CanonicalStateHasher.get_hash`. "fm" was read as frontier_marches.

| world | side | hash | classification |
|---|---|---|---|
| frontier_marches | new | 8dd82ff4e53692f1e2c5fa2d95f65377b119f6e20addce60a527ea9f4aa4e8a1 | PINNED |
| frontier_marches | main | 8dd82ff4e53692f1e2c5fa2d95f65377b119f6e20addce60a527ea9f4aa4e8a1 | no record (main lacks it) |
| crowded_frontier | new | 3a8bd80eb8ece2d729eeb3aaabfb74d95c779bab8f32a983747d6316812753b9 | PINNED |
| crowded_frontier | main | 3a8bd80eb8ece2d729eeb3aaabfb74d95c779bab8f32a983747d6316812753b9 | no record |

Both pairs hash-equal: the record is outside hashed state.

`_run_engine` run (frontier_marches s42, 100 ticks): record = ResourceGovernor, ConcurrentExecutionAdapter, 100 ms, audit_mode false, no_frame_pacing true: NOT_PINNED. The helper refused it:
"run frontier_marches_42_100_3759105_93be1e5e is NOT_PINNED and cannot be reported as behaviour evidence: governor is 'src.engine.governor.ResourceGovernor', pinned is 'tests.helpers.kernel_pinning.PinnedNormalGovernor'; executor is 'src.engine.executor.ConcurrentExecutionAdapter', pinned is 'src.engine.executor.LocalSequentialExecutor'; max_tick_budget_ms is 100.0, pinned is at least 1e+09; audit_mode is False, pinned is True"

## Positive control for the advisory
It flags 18 lines in TCK-20261031-A-RETREAT-PROJECT-OUTLIVES-ITS-THREAT/evidence (the `_run_engine` probes that cost the day).

## Known limits
- The record exists only when the kernel has an artifact repository (observability mode not OFF). An OFF run has no manifest, classifies NOT_PINNED, and `arm_child` refuses it: correct, since nothing shows it was pinned.
- `PINNED.governor` names `tests.helpers.kernel_pinning.PinnedNormalGovernor` by module path; if that helper moves, the classifier moves with it. `test_the_pinned_definition_matches_what_build_kernel_builds` holds that.
- The advisory sees only evidence scripts stored in the repo; lane scratch outside it is covered by the manifest record and the helper, not by the scan.
- The record says what the kernel was built with; it does not claim the pinned world is the production path's world (that is the executor parity tests).
