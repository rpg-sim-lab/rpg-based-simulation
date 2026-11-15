---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261115-PAIRED-PASS-RECORDS-THE-HOLD-LINE-AND-CHECKS-ITS-BASE
phase: open
date: 2026-11-15
tags: [determinism, benchmarking]
---

# TCK-20261115-PAIRED-PASS-RECORDS-THE-HOLD-LINE-AND-CHECKS-ITS-BASE

## Title
The paired measurement records a spy's data in the same pass, proves the spy changes nothing with plain-twin controls, and refuses a fix arm that is not built on the announced base

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
rpg-designer ruled on two measurement time cuts (#634 6891590806, verbatim in `agent-working/staging_artifacts/TCK-20261115-PAIRED-PASS-RECORDS-THE-HOLD-LINE-AND-CHECKS-ITS-BASE/rpg_designer_ruling_2026-11-15.md`; owner approval #715 6891576449; lead-planner asked for one standard ticket).

(a) **A shared daily base is accepted.** Its validity rests on `git merge-base <fix> <main>` equalling the announced base sha, not on the base's age. The 24 h limit is a scheduling cap only. The cache key includes the spy sha.

(b) **The hold line (or any spy's data) is recorded during the paired pass.** The minimum control is at least 3 spied fix-arm cells, one per world, with seeds rotated per run. Each must hash-equal a plain, unspied twin re-run. The base arm gets one control cell when its cache is first built. A failed control voids the whole pass: the deaths result as well as the spy data.

Why now: the group-combat check (TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET) held ubuntu's one heavy slot for about 9 h. About 2.5 h of that was a second pass that re-ran 15 cells only to collect hold-line data (`/data/vboxuser/Work/groups_base/measure_pair/run_pair.sh`, Phase 2).

## Scope
1. **Spy hook in paired's child path.** `tools/rpg_measure/paired.py` takes `--spy <path>`.
   - `tools/rpg_measure/arm_child.py` loads it in both arms. The spy wraps functions read-only, as `group_hit_spy.py` does: it calls the real function and returns its result unchanged.
   - The spy's output is written beside the arm result, e.g. `<world>_<seed>.spy.json`.
   - The spy's contract (what it exposes, what it may not do) is written once, in the paired module docstring.
   - The first spy is the hold-line spy, generalised from `agent-working/staging_artifacts/TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER/group_hit_spy.py` (on branch rpg-ubuntu-group-combat-attackers, 437160ac3).
2. **Cache key.** A result's key is the base or fix sha, the child hash (runner version), world, seed, ticks, and the spy sha: the sha256 of the spy file, or `none` with no spy. A result cached under one spy is never read under another, or under no spy.
3. **Plain-twin controls.**
   - With `--spy`, paired re-runs at least 3 fix-arm cells without the spy, one per world. Seeds rotate per run, by a rule written down and recorded in the report.
   - One base-arm cell is re-run the same way whenever the base arm is first built under that spy key.
   - Each twin's final hash must equal its spied cell's. Any mismatch voids the pass: outcome `VOID` (or `REFUSED` with that detail, whichever the run-ledger schema allows), no verdict table, and the mismatched cells named. Exit non-zero, never 0.
4. **Base announcement and merge-base check.**
   - paired prints and records the base sha and the fix sha.
   - Before any run, it refuses with exit 2 unless `git merge-base <new> <main ref>` equals the base sha.
   - The main ref defaults to `origin/main`, and `--main-ref` overrides it. No other override and no path-scoped exemption.
5. **Spy verdict in the report.** The spy may supply a comparison (e.g. the hold line: STOP when a cell's new arm has more qualifying holds than its base arm, rpg-designer ruling #634 6884784984). paired prints it beside the deaths table, and a spy STOP is part of the outcome.
   - The hold-line rule must be quoted from its ruling, not re-derived. The rule as run today is in run_pair.sh: a no-hit hold of 50+ ticks, or a hold in force at the last tick, new against base.
6. **Rule text for docs/guides/delivery_process.md**, measurement section, after "### Behaviour evidence comes from the pinned runner". Proposed wording below. That doc is unowned, so the wording routes through the leads before it lands; it is not edited by this ticket's implementer alone.
7. Tests (tests/tools or the existing rpg_measure tests):
   - the spy sha in the key;
   - a mismatching twin voids the pass;
   - merge-base refusal, and acceptance at equal;
   - seed rotation recorded;
   - a no-spy run is unchanged: same cache paths as today except the added `none` component, same report.
   - Positive controls: a deliberately state-changing test spy must be caught by the twin check, and a fix not on the base must be refused.

## Out of Scope
- The GitHub Actions runner proposal (owner's step 3; the designer wants the rule first). Separate.
- Changing the death bar (D76 plus the 2026-11-11 Tier 1/2 ruling stay as is).
- Timing measurements (docs/engine/performance_contract.md), unchanged.
- Approving a spy. That is rpg-designer's per spy sha; the tool records the sha, and a human decides.
- `--collected` mode: the ticket states whether spy results and controls are supported there, or refused with a reason. Plan decides; no silent half-support.
- Re-running the group-combat check. Its run (ghpair, 2026-11-15) finishes as specced under run_pair.sh.

## Acceptance Criteria
1. `paired --spy <path>` writes each arm's spy data in the same pass as its deaths result. For one world x seed, the spied fix cell's final hash equals today's unspied result hash; shown on one real cell.
2. The cache key includes the spy sha, shown by a test where the same base sha under two spies gives two cache entries.
3. At least 3 fix-arm plain twins, one per world, with seeds rotated and recorded, plus 1 base twin on the base arm's first build. A forced mismatch gives a void outcome, a non-zero exit, and no verdict.
4. A fix arm whose merge-base with the main ref differs from the base sha is refused before any run, with exit 2 and both shas printed.
5. The hold-line spy reproduces the ghpair Phase 2 numbers on at least one cell from its saved outputs (`/data/vboxuser/Work/groups_base/measure_pair/out/spy_new_*.json`), when those exist.
6. The delivery_process.md rule text is agreed by the leads and lands, citing #634 6891590806 and #715 6891576449.
7. Scoped tests pass. The Bible and parity ledger are untouched (tooling only). The run data each test wrote is cleaned by run id.

## Proposed rule text (docs/guides/delivery_process.md, new subsection; routes via the leads)

> ### A paired result is valid for the base it was built on (rpg-designer, #634 6891590806; owner #715 6891576449)
> A paired measurement proves a ticket's effect on the base its fix was built from. So `git merge-base <fix> <main>` must equal the announced base sha, and `paired` refuses otherwise. Several tickets may share one cached base arm. The 24 h limit on a shared base is a scheduling cap, not a validity test. If anything that can change a simulation hash (`src/**`, `data/**`, `config/**`) lands on main after the base, a ticket measured on that base must, before merge, do one of three things:
> 1. land in the same batch as that change, both measured on the shared base;
> 2. show the change is behaviour-neutral (new main's plain hash equals the base's on the standard cells);
> 3. rebase and re-pair.
>
> No path is exempt. A spy that records extra data runs inside the paired pass, read-only. At least 3 spied fix-arm cells (one per world, seeds rotated and recorded), plus one base cell when the base arm is first built, are re-run without the spy and must hash-equal. One mismatch voids the whole pass, deaths result included, and the spy goes back to its author. A spy is approved by its sha, and a changed spy needs approval again.

## Related Tickets
- TCK-20261015-STANDARD-PAIRED-MEASUREMENT-COMMAND-FOR-BEHAVIOUR-STEPS (done): the paired tool.
- TCK-20261026-PAIRED-COMPARES-COLLECTED-OFF-HOST-RESULTS (done): `--collected`.
- TCK-20261023-PAIRED-ARMS-RUN-WITHOUT-THE-PER-TICK-REPLAY-DIGEST (todo, OPEN): also edits the paired child path; check order and overlap before planning.
- TCK-20261023-PAIRED-WRITES-ONE-RUN-LEDGER-ROW-PER-INVOCATION (todo, OPEN): run-ledger outcome values; a VOID outcome must fit its schema.
- TCK-20261103-A-MEASUREMENT-NOT-ON-THE-PINNED-RUNNER-CALLS-ITSELF-EVIDENCE (#918): `require_pinned` in arm_child.py.
- TCK-20261101-A-HOSTILE-ATTACKING-YOU-OUTRANKS-THE-GROUP-SHARED-TARGET / TCK-20261103-A-GROUP-HIT-RECORDS-ONLY-ITS-FIRST-ATTACKER: the source of the hold-line spy.

## Related Docs
- docs/guides/delivery_process.md ("Behaviour evidence comes from the pinned runner")
- docs/plans/test_architecture/reference/run_ledger.md (paired hook rules; testing's)

## Related Stored Artifacts
- agent-working/staging_artifacts/TCK-20261115-PAIRED-PASS-RECORDS-THE-HOLD-LINE-AND-CHECKS-ITS-BASE/rpg_designer_ruling_2026-11-15.md (verbatim ruling)

## Related Code Areas
- tools/rpg_measure/paired.py, tools/rpg_measure/arm_child.py, tools/rpg_measure/stats (verdicts)
- tools/test_architecture/run_ledger.py (testing's; an outcome value change routes to testing-planner)

## Assumptions / Open Questions
- Q1: do the run-ledger outcome values allow VOID? If not, it is REFUSED with a detail, or testing-planner adds VOID. Ask before building.
- Q2: the seed-rotation rule. Proposed: control seed index = (run counter or the date's ordinal) mod the seed count, per world offset by the world's index. Recorded in the report either way.
- Q3: the hold-line rule is quoted from #634 6884784984 at planning (fetch the body; do not paraphrase).
- Assumption: wrapping read-only functions does not change the state hash. The cell run on 2026-11-15 showed MATCH on both arms (crowded s42 2000t); the twin controls are what prove it each time.

## Implementation Notes
Size estimate: medium. About 150-250 lines in tools/rpg_measure plus tests, no src/ change, no heavy run beyond one real cell for AC1/AC5 (that cell needs lead's go and the heavy slot). Dispatch is the owner's, via lead-planner.

## Test Summary
(not started)

## Files Changed
(not started)

## Completion Summary
(not started)
