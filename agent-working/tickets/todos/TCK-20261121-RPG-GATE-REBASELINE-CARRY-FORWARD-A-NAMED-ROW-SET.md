---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261121-RPG-GATE-REBASELINE-CARRY-FORWARD-A-NAMED-ROW-SET
phase: open
date: 2026-11-21
tags: []
---

# TCK-20261121-RPG-GATE-REBASELINE-CARRY-FORWARD-A-NAMED-ROW-SET

## Title
`rebaseline --carry-forward`: record a main run's candidate for every row except a named set that keeps its previous value, with per-row provenance, and let the report still judge the carried rows

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Raised by lead-planner-u24 on the owner's choice A (#715 7063603750), filed by testing-planner as the lasting fix. While a re-record must move the harness hash (TCK-20261121-RPG-GATE-REBASELINE-AFTER-THE-NONE-KIND-GROUP-HASH-MOVE), some moved rows may be held until a trace explains them (the first case is frontier_living_world meat O3.attacks_on_people, 0.6 to 24, ruled a bug candidate by rpg-designer). Today `rebaseline` has no partial form (read, not run): it takes the whole candidate, an outcome row cannot be left out, and the only exclusion is a validity fail owned by a current `state: fail` known entry (`omitted_validity`). A hand-edited candidate is a typed baseline, which the baseline law forbids. This ticket adds the partial form as a tool feature. Filing only; nothing is built here.

## Scope
Design to settle in the plan (testing-planner, before any build):
1. A `--carry-forward <selectors>` option on `rebaseline` (tools/test_architecture/rpg_gate_baseline.py). A selector names rows by (id, scope, world, group, tick, key) with fnmatch. Each carried row is copied from the previous baseline instead of taken from the candidate. A selector that matches no previous row refuses; so does a selector that matches no candidate row (nothing to hold); a carried row also present in the candidate is recorded as the previous value and the candidate's value is kept in the `rebaseline` record for the diff.
2. Provenance per carried row: `carried_from: {version, commit_sha, run_id}` on the row, and a `carried` list in the file's `rebaseline` record with the reason, the ticket and the owner ruling reference. A carried row is never described as measured at the new sha or hash. The lint rejects a carried row without `carried_from`, a carried row whose source version does not exist, and a carry-forward without a ticket and an owner ruling.
3. The report keeps JUDGING carried rows: a carried row is compared like any other row, so a current run that moves off the held value reads as `drift` (or `pass` inside its threshold), not `stale`/`no-data`. The report marks the row as carried in the markdown and JSON so a pass on a carried value is visible as such.
4. Thresholds: a carried row keeps its previous `k` and `floor` (the thresholds come from the reference row; `rpg_gate_baseline_format.md`, "Thresholds come from the reference").
5. Optional, separable: a world-scoped `drift` entry in `known_reds.py` (`cases: [{world}]`), so a trace ticket can own one world's drift on a row without covering the same metric in the other worlds. Today `drift` entries match on `<metric_id>[:group]` only and `cases` is allowed on `fail` entries only. Decide in the plan whether this rides here or gets its own ticket.
6. The candidate guard stays exactly as it is: only a main CI run's own candidate (ci run, ref refs/heads/main, not evidence_only, known-file sha present) is a baseline source. Carry-forward reads the previous baseline from the repository only; it does not widen what a candidate may be.

Open design point (settle in the plan): a carried row's value is measured at an older sha than the file's `commit_sha`. The file-level provenance must say so without a reader having to diff versions; the plan names the field and the lint.

## Out of Scope
- Changing the candidate builder or the main-run-only guard.
- Hand-editing any baseline or candidate.
- The re-record itself and the attribution of the moved rows (their own tickets).
- Choosing which rows to hold: the owner's call, per re-record.
- Anything in `src/`.

## Acceptance Criteria
1. `rebaseline --carry-forward` records the candidate for all rows except the selected set, which keeps the previous baseline's values, and writes `carried_from` per carried row plus a `carried` list in the `rebaseline` record.
2. The lint refuses a carried row without `carried_from`, a missing source version, a selector that matches no row, and a carry-forward without a ticket and an owner ruling reference.
3. The report judges a carried row against its held value (drift or pass, not stale) and labels it carried in the markdown and JSON.
4. A test pins that a candidate that is not a main CI run's own is still refused with `--carry-forward`.
5. The format doc (`rpg_gate_baseline_format.md`) and `baseline_change_policy.md` describe carried rows and say a carried row is not a measurement at the new sha.
6. Tests: carried row keeps the old value and thresholds; non-carried rows take the candidate's; selector edge cases; the report on a run that moves off the held value reads drift.
7. If item 5 of the Scope rides here: a drift entry with `cases: [{world}]` owns only that world's drift; an unscoped entry keeps its meaning.

## Related Tickets
- TCK-20261121-RPG-GATE-REBASELINE-AFTER-THE-NONE-KIND-GROUP-HASH-MOVE (the re-record this feature would serve; the owner chose to hold the whole re-record for now, #715 7063603750)
- TCK-20261121-RPG-GATE-METRICS-REJECT-A-NON-EATING-KIND-GROUP-AS-UNDECLARED (the hash move)
- TCK-20261019-RPG-GATE-DRIFT-JUDGED-ON-THE-REFERENCE-THRESHOLD (thresholds come from the reference row)
- TCK-20261023-RPG-GATE-CANDIDATE-RECORDS-ITS-CI-RUN-AND-KNOWN-FILE (the main-run-only guard this keeps)

## Related Docs
- `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md`
- `docs/plans/test_architecture/reference/baseline_change_policy.md` (rules 8, 9, 10, 12)

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/test_architecture/rpg_gate_baseline.py` (`rebaseline`, the lint, `resolve_references`)
- `tools/test_architecture/rpg_gate_report.py` (`_compare`, `_outcome`)
- `tools/test_architecture/known_reds.py` (only if item 5 rides here)

## Assumptions / Open Questions
- Mechanics read from the code, not run. Size estimate (testing-planner, to lead-planner-u24): about 150-250 lines plus tests, one batch.
- Whether the world-scoped drift entry rides here or gets its own ticket.
- Whether a carried row should expire (force a re-measure by a date) or stay until the next re-record; the owner's call.
- A carried baseline keeps the milestone question open: see the milestone reading in the re-record ticket's thread (`--milestone` and `resolve_references`).

## Durable state, lifecycle and clocks
The baseline file is the durable artefact; this feature adds per-row provenance to it. Lifecycle: a carried row lasts until the next re-record that does not carry it.

## Implementation Notes
Filing only.

## Test Summary
Not applicable.

## Files Changed
This ticket only.

## Completion Summary
Open.
