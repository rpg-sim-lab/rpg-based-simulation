---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261121-RPG-GATE-A-BASELINE-CAN-BE-NAMED-ITS-MILESTONES-REFERENCE
phase: done
date: 2026-11-21
tags: []
---

# TCK-20261121-RPG-GATE-A-BASELINE-CAN-BE-NAMED-ITS-MILESTONES-REFERENCE

## Title
A baseline can be named its milestone's reference (`milestone_reference`), set only by `rebaseline` citing an owner-ruling comment on #715, so a re-record inside M1 does not leave the stale first baseline as the fixed reference

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
OWNER ANSWER (#715, relayed by lead-planner-u24): add the marker; the label stays M1; only `rebaseline` may set it, and only citing an owner-ruling comment on #715. `baseline_change_policy.md` rule 10 says the fixed reference is "the first version of the current milestone, or the version a milestone owner names", but the code implements only the first half (read, not run): `resolve_references` in `tools/test_architecture/rpg_gate_baseline.py` takes the LAST baseline and the lowest version whose `milestone` equals the last one's. A v3 recorded as `--milestone M1` therefore leaves v2 (harness hash 5a7f14, stale against the current harness) as the milestone-first reference, and `_compare` in `rpg_gate_report.py` returns `stale` for a stale reference without judging, so every outcome row would read stale, never pass, until the milestone changes. This ticket implements the second half of rule 10. Filing only; it lands before the re-record (TCK-20261121-RPG-GATE-REBASELINE-AFTER-THE-NONE-KIND-GROUP-HASH-MOVE).

## Scope
1. A baseline field `milestone_reference` (boolean, optional, default absent = false) on the baseline document.
2. `rebaseline` gains a `--milestone-reference` flag. It is refused unless an owner ruling is cited (`--owner-ruling-ref`, `--owner-ruling-date`, the existing arguments and `_ruling_problem` check), and the cited reference must be an owner-ruling comment on #715 (the check the plan names: the existing ruling-reference shape, or a stricter one for this flag). The flag writes `milestone_reference: true` on the new baseline only; it never edits an existing file (`rebaseline` already never modifies one).
3. `resolve_references`: milestone-first = the last baseline of the last one's milestone that carries `milestone_reference: true`; when none does, the first of the milestone as today (an unmarked milestone behaves exactly as before). Where several carry it, the highest version wins, so a later owner-named reference replaces an earlier one. A marker on a baseline of another milestone has no effect.
4. The lint accepts and validates the field (boolean only; a marker without a recorded owner ruling on that baseline is refused).
5. The report prints which baseline is the milestone-first reference and why (`first of milestone` or `named by owner ruling <ref>`), so a reader can see it.
6. `rpg_gate_baseline_format.md` and `baseline_change_policy.md` (rule 10) say the field exists and who may set it.

## Out of Scope
- Hand-setting the marker on an existing baseline.
- Any change to staleness rules or to what a stale reference yields (still `stale`, never `pass`).
- The carry-forward option (TCK-20261121-RPG-GATE-REBASELINE-CARRY-FORWARD-A-NAMED-ROW-SET).
- The re-record itself.

## Acceptance Criteria
1. With v1 (M0), v2 (M1) and a v3 (M1) recorded with `--milestone-reference`, `resolve_references` returns last = v3 and milestone-first = v3, and a run at the current harness hash can read `pass` and `drift`, not `stale` for the reference.
2. Without the marker the behaviour is unchanged: milestone-first is the first baseline of the milestone (existing tests stay green).
3. `rebaseline --milestone-reference` without a cited owner ruling refuses, with a message naming the rule; with one it records the ruling reference on the baseline.
4. The lint refuses a non-boolean marker and a marker without its ruling.
5. A marker on a baseline of another milestone does not move the reference; two markers in one milestone give the higher version.
6. The report names the reference baseline and the reason.
7. The format and policy docs are updated in the same change.

## Related Tickets
- TCK-20261121-RPG-GATE-REBASELINE-AFTER-THE-NONE-KIND-GROUP-HASH-MOVE (needs this first; its v3 is to be named M1's reference)
- TCK-20261121-RPG-GATE-REBASELINE-CARRY-FORWARD-A-NAMED-ROW-SET (independent; the order is marker, carry-forward if rows are held, re-record)

## Related Docs
- `docs/plans/test_architecture/reference/baseline_change_policy.md` (rules 8-12; rule 10 is the text this implements)
- `docs/plans/test_architecture/reference/rpg_gate_baseline_format.md` ("Dual reference")

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/test_architecture/rpg_gate_baseline.py` (`resolve_references`, `rebaseline`, the lint, `_ruling_problem`)
- `tools/test_architecture/rpg_gate_report.py` (the references line, `_compare`)

## Assumptions / Open Questions
- Mechanics read from the code, not run. Size estimate: about 60-120 lines plus tests; one small batch.
- The exact ruling-reference check (a #715 comment id, as the owner worded it) is settled in the plan against what `_ruling_problem` validates today.

## Durable state, lifecycle and clocks
The baseline file is the durable artefact; `milestone_reference` is one added field on a new baseline. It lasts until a later marked baseline of the same milestone replaces it.

## Implementation Notes
`milestone_reference` (optional boolean) on the baseline; `rebaseline(milestone_reference=True)` / `--milestone-reference` writes it on the new file only and refuses (rule 10 named) without an owner ruling or with a ref that does not fullmatch `#715 <digits>` (`MILESTONE_RULING_REF_RE`, the shape v2 records). `resolve_references` picks the highest marked baseline of the last one's milestone, else the first; `References.milestone_reason` carries the reason; the report adds `references[].reason` and prints it. The lint refuses a non-boolean marker and a true marker without a #715 ruling on that baseline (v1 top-level, later in `rebaseline.owner_ruling`). Peer's added requirement (the #715 check) is in. No baseline, known file or gate config touched.

## Test Summary
tests/unit/tools/test_rpg_gate_baseline.py and test_rpg_gate_report.py: 167 passed. New tests cover ACs 1-6 and the #715 shape (7 refused refs). Mutation-checked six ways (take lowest marked, drop the milestone filter, drop the #715 regex, drop the lint ruling check, drop the boolean check, drop the rebaseline refusal): each failed at least one test.

## Files Changed
tools/test_architecture/rpg_gate_baseline.py, tools/test_architecture/rpg_gate_report.py, tests/unit/tools/test_rpg_gate_baseline.py, tests/unit/tools/test_rpg_gate_report.py, docs/plans/test_architecture/reference/baseline_change_policy.md, docs/plans/test_architecture/reference/rpg_gate_baseline_format.md, this ticket.

## Completion Summary
Rule 10's second half is implemented; the re-record can name v3 as M1's reference once this merges.
