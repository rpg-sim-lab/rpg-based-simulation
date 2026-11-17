---
status: historical
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261116-RE-BASELINE-THE-RPG-GATE-REFERENCE-TO-A-MAIN-RUN-AFTER-M1-BASE
phase: done
date: 2026-11-16
tags: []
---

# TCK-20261116-RE-BASELINE-THE-RPG-GATE-REFERENCE-TO-A-MAIN-RUN-AFTER-M1-BASE

## Title
Re-baseline the rpg regression gate's reference to a main run after M1-base, so Milestone 1's outcome rows stop reading "stale"

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P1

## Request Summary
Both M0 references of the rpg gate ("last" and "milestone-first", rpg_gate_v1.json) were stale on the harness hash (525fe36f vs 5a7f1459), so all 253 outcome rows of every gate run read "stale" and said nothing per step. rpg-designer ruled the reference a separate owner ask. The owner chose (a), re-baseline through the standard path (#715 6920465555). Run 43840618903, pinned to 9c398a068 by a ref input, wrote an evidence-only candidate, which `rpg_gate_baseline rebaseline` refuses with no override, so the owner chose a re-dispatch on main with no ref input (#715 6920528237): run 43895014837 at e72270894.

## Scope
- Write `tests/simulation_quality/rpg_gate/baselines/rpg_gate_v2.json` with the standard `python -m tools.test_architecture.rpg_gate_baseline rebaseline`, from run 43895014837's candidate (`agent-working/lead/evidence/rpg-gate-candidate-e72270894.json`, on main since #947 6034ea7c0, committed byte for byte by the ubuntu lead; sha256 3934db8e6d0c8b886b132cb562b890c5856a2c2defa402588adb440ce650fdc2), with --known, --memo-row (row 97), --pr, the owner ruling and a cite carrying the s42-only disclosure.
- Roadmap §12.5 Base line and memo row 97.

## Out of Scope
- Any edit to v1, to the gate, its config or its stop lines.
- Any validity normalisation (the tool refuses it anyway).

## Acceptance Criteria
- The tool writes v2 without refusal; v1 is unchanged; `rpg_gate_baseline lint` is clean.
- v2's provenance names run 43895014837 (refs/heads/main) and e72270894; its cites include the PR, memo row 97 and "src identical to 6b59284ee, shown hash-neutral against M1-base 9c398a068 at s42 only (owner 6917174751)".
- Its content equals the recorded dry run apart from the PR field and the recorded_at/stale_after times.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC; TCK-20261019-RECORD-BASELINE-V1 (v1)

## Related Docs
- docs/plans/systemic_world/roadmap.md §12.5; docs/plans/systemic_world/owner_decision_memo.md row 97

## Related Stored Artifacts
None.

## Related Code Areas
- tools/test_architecture/rpg_gate_baseline.py (read only); tests/simulation_quality/rpg_gate/baselines/

## Assumptions / Open Questions
- The PR number is needed by the tool, so v2 is written in a follow-up commit of the same PR, after the PR exists (lead-planner-u24's two-part ask).

## Implementation Notes
- Dry run 2026-11-16 into a scratch copy of baselines/: accepted; v2, milestone M1, 274 metric rows, 3 omitted validity rows (owned by the V1 free-meal entry), 0 undefined, 101 rows changed vs v1, 0 stop lines crossed; lint clean.

- The command (dry run used --dir <scratch copy> and --pr "#DRYRUN"): `python3 -m tools.test_architecture.rpg_gate_baseline rebaseline --candidate agent-working/lead/evidence/rpg-gate-candidate-e72270894.json --config tests/simulation_quality/rpg_gate/config.yaml --dir tests/simulation_quality/rpg_gate/baselines --known tools/test_architecture/rpg_gate_known.yaml --memo-row "owner_decision_memo row 97" --pr "#N" --milestone M1 --cite "rpg gate run 43895014837 on main e72270894; src identical to 6b59284ee, shown hash-neutral against M1-base 9c398a068 at s42 only (owner 6917174751)" --owner-ruling-ref "#715 6920465555" --owner-ruling-date 2026-11-16`.

## Test Summary
- `python3 -m tools.test_architecture.rpg_gate_baseline rebaseline ... --pr "#948"` wrote `rpg_gate_v2.json` with no refusal. The candidate is `agent-working/lead/evidence/rpg-gate-candidate-e72270894.json` (sha256 3934db8e…, on main since #947).
- v2 equals the two dry runs (first from the lead branch's copy, then from main's) apart from the PR cite and the recorded_at/stale_after times: version 2, milestone M1, commit e72270894, ci run 43895014837 refs/heads/main, 274 metric rows, 3 omitted validity rows (owned by the V1 free-meal entry), 0 undefined, 101 rows changed vs v1, 0 stop lines crossed; owner_ruling #715 6920465555 (2026-11-16).
- `rpg_gate_baseline lint` rc 0 with v1 and v2 present; v1 is unchanged.
- Earlier on this branch: `tests/unit/tools/test_known_reds.py` and `tests/unit/tools/test_rpg_gate_baseline.py`, 125 passed (-n 1).

## Files Changed
- `tests/simulation_quality/rpg_gate/baselines/rpg_gate_v2.json` (new; written by the tool, never hand-edited)
- `docs/plans/systemic_world/roadmap.md` (§12.5 Base line) and `docs/plans/systemic_world/owner_decision_memo.md` (row 97), earlier on this PR's branch
- this ticket

## Completion Summary
Done 2026-11-17 in PR #948, the second of its two owner-approved parts (#715 6935497929). The gate's reference is now v2, recorded from main run 43895014837 at e72270894. Its src is identical to 6b59284ee, shown hash-neutral against M1-base 9c398a068 at s42 only (disclosed in v2's cites). From the next gate run on, Milestone 1's outcome rows read against v2 instead of "stale"; v1 stays as the history record. Report-only under M1 pace.
- Known gap: the reference's commit is main e72270894, not 9c398a068 itself; the two are proven equal only at s42, not at s43-46.
