---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-CHECKS-EACH-KIT-ON-BOTH-FROZEN-TREES-BEFORE-ITS-RUN
phase: open
date: 2026-11-18
tags: []
---

# TCK-20261118-A-DIAGNOSTIC-KIT-PREFLIGHT-CHECKS-EACH-KIT-ON-BOTH-FROZEN-TREES-BEFORE-ITS-RUN

## Title
An automatic preflight for every measurement kit (spy, probe, runner, summarizer): sha, import, a short fixture run and field liveness on both frozen trees, with its output in the S9 packet

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P1

## Request Summary
Owner direction #715 6971915608, item 2. On 2026-11-18 two kit faults reached S9 records, and rpg-designer caught both by reading:
- the #955 divergence probe read `navigation.failure_reason` (not a real field), so field 6 was always None;
- the gate spy's `ctx` vs `context` keyword. Under PERC-02a rule 4, its TypeError could be swallowed as "not perceived".
Others the same day: `python -I` with PYTHONPATH (no import), and a runner not writing a `driver_rc=` line that its summarizer reads. The check should be automatic, not more manual review.

## Scope
`tools/rpg_measure/kit_preflight.py` (stdlib only, like env_digest.py), plus a kit manifest (JSON beside the kit: each file with its sha256, entry command, expected output fields, guard-line regex). Run as `kit_preflight.py <manifest> --tree <A> --tree <B> --ticks 10`. Checks:
(a) every kit file named in the manifest exists at its sha;
(b) each kit script imports on BOTH frozen trees under the exact interpreter flags the run uses (python -I, cwd = the tree);
(c) a short fixture run (5-10 ticks) of each process succeeds on both trees, with rc 0;
(d) every recorded field is present, and NOT constant None or default across all entities and ticks in the fixture output. A field the manifest declares "may be constant" is listed explicitly;
(e) the guard lines are present and OK; root ERROR+ logs are 0; the wrapper/hook coverage the kit claims is hit at least once.
Output: a PASS/FAIL table with the input shas, pasted into the S9 packet with the evidence label "executed". The preflight run itself is a small diagnostic run on the frozen trees under its own S9 line.

## Out of Scope
- Judging a kit's design (still rpg-designer's read).
- Any run longer than the fixture.

## Acceptance Criteria
- Run on today's two faulty kit versions, the preflight FAILS on (d) for the d4a5e6a8 probe's field 6 and on (b) for the -I import. A regression test pins both with small synthetic fixtures.
- A clean kit passes on both trees in under 2 minutes of host time.
- docs: the S9 packet template (rpg-planner handover and tools/rpg_measure README or docstring) names the preflight line and the evidence labels inspected / executable / executed / validated.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC (the S9 runs it serves)

## Related Docs
- tools/rpg_measure/ (env_digest.py, paired.py: existing patterns)

## Related Stored Artifacts
- /mnt/data2/rpg-measure/ci955/kit_approved/ (the corrected kit), /tmp/claude-1000/probe/ (the faulty versions, if still present)

## Related Code Areas
- tools/rpg_measure/

## Assumptions / Open Questions
- Cost estimate (rpg-planner): about 200 lines plus about 100 of tests, one lane for 2-3 hours; per-kit run cost under 2 minutes of host time.
- Whether the manifest is hand-written or generated from the runner's command lines.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
