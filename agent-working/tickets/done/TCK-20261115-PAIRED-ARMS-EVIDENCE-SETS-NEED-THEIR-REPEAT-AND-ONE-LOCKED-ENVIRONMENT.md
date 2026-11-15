---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261115-PAIRED-ARMS-EVIDENCE-SETS-NEED-THEIR-REPEAT-AND-ONE-LOCKED-ENVIRONMENT
phase: done
date: 2026-11-15
tags: [testing, determinism]
---

# TCK-20261115-PAIRED-ARMS-EVIDENCE-SETS-NEED-THEIR-REPEAT-AND-ONE-LOCKED-ENVIRONMENT

## Title
A paired-arms evidence set carries its base-vs-base repeats and was built under one recorded environment with a known dependency lock

## Status
DONE

## Tier
hotfix

## Type
feature

## Priority
P2

## Request Summary
Child of TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST: its ACs 6-8 as built, plus the missing-lock refusal added in testing-planner's review. Source: rpg-designer's runner-evidence rule (#634 items g, h, i) and rpg-planner's env8 ruling (lead relay, 2026-11-15). Owner scope: #715 6893752032 (A), build only, no runs; the dispatch (B) is a separate ask.

## Scope
- `paired_arms plan --evidence` and the workflow `evidence` input (default true).
- `uv_lock` (sha256 of the tool checkout's uv.lock) in the runner identity, and its comparison at assembly.
- `paired.py` cache key `<sha12>-<child8>-<ticks>-<env8>[-repeat]` built from ordered components, `env.json` per result dir, `--collected` environment refusals.
- Fail-closed on a lock that is not a sha256.

## Out of Scope
- The plain-twin control and any spy hook (AC9 of the parent, held for TCK-20261115-PAIRED-PASS-RECORDS-THE-HOLD-LINE-AND-CHECKS-ITS-BASE).
- Any dispatch or run (parent AC1, AC10).

## Acceptance Criteria
- [x] AC1 (parent AC6, g): `plan --self-check off` is refused for an evidence dispatch; seed42 and full still plan the repeat jobs; the workflow passes the input through (tested).
- [x] AC2 (parent AC7, h): the runner identity carries the sha256 of the tool checkout's uv.lock; assembly refuses jobs, or the arms of a key, that differ in it (tested on fake artifacts).
- [x] AC3 (parent AC8, i): the key is `<sha12>-<child8>-<ticks>-<env8>[-repeat]` from `key_components`; env.json per result dir; `--collected` refuses a missing or mismatched env.json and mixed environments; an old-format entry is a miss and kept; the five named tests exist.
- [x] AC4 (review): a lock that is not a 64-hex sha256 (e.g. "missing") is refused at assembly, in the `--collected` environment check, and by local paired / `run-arm` before caching (one test per point).

## Related Tickets
- TCK-20261023-PAIRED-ARMS-RUN-OFF-THE-SHARED-HOST (parent, stays inprogress)
- TCK-20261115-PAIRED-PASS-RECORDS-THE-HOLD-LINE-AND-CHECKS-ITS-BASE (owns the spy key component)

## Related Docs
- docs/plans/test_architecture/reference/paired_arms_off_host.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/test_architecture/paired_arms.py, tools/rpg_measure/paired.py (rpg's file, rpg-planner's env8 ruling), .github/workflows/paired-arms.yml

## Assumptions / Open Questions
- rpg-planner and rpg-planner-ubuntu review paired.py before the push ask.
- The arm-tree uv.lock fallback exists in `uv_lock_digest(arm_tree=)` but no flow passes a tree.

## Implementation Notes
Commits cb37b8a48 (AC1), 5f754072b (AC2), 3ef5ca62f (AC3), then the fail-closed fix. See the parent ticket's Implementation Notes for the choices (the `evidence` input default; the CI runner label is the image, not RUNNER_NAME).

## Test Summary
tests/unit/tools/test_paired_env_key.py, test_paired_arms.py, test_rpg_measure.py, test_rpg_measure_collected.py and tests/static/test_ci_paired_arms_workflow_shape.py pass; no run of any kind.

## Files Changed
- tools/test_architecture/paired_arms.py, tools/rpg_measure/paired.py, .github/workflows/paired-arms.yml
- tests/unit/tools/test_paired_env_key.py (new), test_paired_arms.py, test_rpg_measure_collected.py, tests/static/test_ci_paired_arms_workflow_shape.py
- docs/plans/test_architecture/reference/paired_arms_off_host.md

## Completion Summary
Built in the parent's branch; closed here so the PR closes a ticket while the parent stays open for its dispatch ACs.
