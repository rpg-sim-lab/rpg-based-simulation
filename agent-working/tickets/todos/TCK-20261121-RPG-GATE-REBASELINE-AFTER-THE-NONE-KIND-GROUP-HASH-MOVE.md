---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261121-RPG-GATE-REBASELINE-AFTER-THE-NONE-KIND-GROUP-HASH-MOVE
phase: open
date: 2026-11-21
tags: []
---

# TCK-20261121-RPG-GATE-REBASELINE-AFTER-THE-NONE-KIND-GROUP-HASH-MOVE

## Title
Re-record the rpg gate baseline from a main run after the `none` kind-group change moves the harness hash

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Steps 2-4 of the plan in TCK-20261121-RPG-GATE-METRICS-REJECT-A-NON-EATING-KIND-GROUP-AS-UNDECLARED. The owner chose "Fix + re-baseline before births" on #715 (comment 7056998775 per lead-planner's relay), which approves the re-record inside M1. Once the config and metric change merge, `harness_hash` differs, every baseline is stale and gives no pass, and the rerun-skip falls back to the full rerun (baseline_format.md, "Staleness").

## Scope
1. After the fix PR merges, dispatch `rpg-gate-report.yml` on main (a CI run, not the local heavy slot). The gate is schedule and dispatch only, so no PR check is blocked while baselines read stale.
2. Build the candidate from that run's documents (`rpg_gate_candidate`); it refuses on a `no-data` document or a `sha` / `harness_hash` / ticks disagreement. Expect no existing row to change value. Declaring `none` in every world (row-set choice (A), 2026-11-21) ADDS zero-valued `none` count rows in all three worlds; they appear in the before/after as appear-only rows and are named in the fix PR body, so they are expected, not a finding. A changed VALUE on an existing row is a finding that goes back to the owner, not an automatic re-baseline (owner, #715).
3. Re-record with `python -m tools.test_architecture.rpg_gate_baseline rebaseline ...`, citing the fix ticket, a memo row and the PR, from a main run (model: #948, bb26e4e5f, run 43840618903 at 9c398a068). No `owner_ruling` is expected if no row changes.
4. A fresh main gate run after the re-record restores the rerun-skip's baseline; its report is read and recorded here.

## Out of Scope
- Editing `rpg_gate_known.yaml`, the config, or any metric.
- Normalising a validity fail by re-baselining (never allowed).
- Re-recording anything but the hash, provenance and the expected appear-only `none` rows if no existing value changed.

## Acceptance Criteria
1. The main run id and head sha used for the candidate are recorded, with the `harness_hash` it carries.
2. The before/after record from `rebaseline` shows only the expected appear-only `none` rows and no changed value on an existing row, or each changed value is reported to the owner before any re-record.
3. The re-record PR cites this ticket, the fix ticket and a memo row; the new baseline is not stale against the current harness.
4. The first gate run on main after the re-record is read: baseline fresh, rerun-skip source run named, `vs_main` fallback empty.

## Related Tickets
- TCK-20261121-RPG-GATE-METRICS-REJECT-A-NON-EATING-KIND-GROUP-AS-UNDECLARED (the change that moves the hash)
- TCK-20261119-RPG-GATE-RERUN-ONLY-NEW-ROWS-AND-A-BASELINE-DIFF-AGAINST-MAIN (the rerun-skip that falls back until this lands)

## Related Docs
- `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md` (Staleness, Re-baseline, Candidate and recording)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/test_architecture/rpg_gate_baseline.py` (`rebaseline`), `rpg_gate_candidate.py`
- `tests/simulation_quality/rpg_gate/baselines/`

## Assumptions / Open Questions
- Whether the re-record PR needs `owner_ruling`: not expected if no row changes; decided by the step 2 result.
- Who runs `rebaseline`: testing-planner plans it; the testing implementer seat is closed, so the author of the PR is to be named when step 1 is reached.

## Durable state, lifecycle and clocks
The baseline file is a durable, versioned, immutable artefact (a new version is written; the old one is kept). Its lifecycle is defined by baseline_format.md; this ticket adds one version.

## Implementation Notes
Filing only. Starts when the fix PR is merged.

## Test Summary
Not applicable.

## Files Changed
This ticket only.

## Completion Summary
Open.
