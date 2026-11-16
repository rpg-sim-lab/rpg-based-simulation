---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-PR-RENDER-REVERT-EVIDENCE-READ-AS-KNOWN-GAP
phase: open
date: 2026-11-16
tags: [delivery, ai]
---

# TCK-20261116-PR-RENDER-REVERT-EVIDENCE-READ-AS-KNOWN-GAP

## Title
`pr_render.py` lists a "Revert evidence" line under Known gaps because the line contains `FAIL`

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
`extract_known_gaps` in `tools/delivery/pr_render.py` (origin/main, about lines 406-415) counts a line in a ticket's Test Summary or
Completion Summary as a gap in two cases: the line contains `FAIL` anywhere, or it begins `Known gap:` after an optional list marker.
A line such as "Revert evidence: with X reverted, 3 tests FAIL" shows that the tests catch the bug. But it contains `FAIL`, so the PR
body lists it under "Known gaps".

testing-planner found this and fixed the bodies by hand on #928, #930, #932, #934 and #937. agent-working-designer-u24 wrote the
draft (main checkout `.claude/handover/drafts/pr-render-revert-evidence-read-as-known-gap-2026-11-16.md`), and
agent-working-planner-u24 checked it against origin/main on 2026-11-16.

## Scope
1. `tools/delivery/pr_render.py`:
   - add a constant `REVERT_EVIDENCE_MARKER = "Revert evidence"` beside `KNOWN_GAP_MARKER`;
   - in `extract_known_gaps`, skip a line whose stripped text, after the optional list marker, starts with `REVERT_EVIDENCE_MARKER`.
     The match is case-sensitive, like `Known gap:`. The skip runs before the `FAIL` and `Known gap:` checks;
   - keep the `FAIL` rule as it is;
   - add one sentence each to the module docstring (lines 23-26) and the function docstring: "A line beginning `Revert evidence`
     is proof a test catches the bug, not a gap, and is skipped."
2. `docs/guides/delivery_process.md`, the paragraph that starts "`pr_render.py` fills that line" (about line 330): add the same
   sentence after the `Known gap:` rule, so the doc and the code agree. Only that paragraph changes; the ride-along wording elsewhere in
   the file is ubuntu agent-working-planner's and stays as it is.
3. `tests/tools/test_delivery_pr_render.py`, 4 tests:
   - a `- Revert evidence: ... 3 tests FAIL` line is not a gap;
   - a plain `2 FAIL (pre-existing)` line is still a gap;
   - a `Known gap: ...` line is still a gap;
   - a ticket whose only `FAIL` line is revert evidence renders `KNOWN_GAPS_NONE_STATED`.

## Out of Scope
- Dropping the `FAIL` substring rule and keeping only `Known gap:`. That would hide real failing-test lines that tickets write today
  without the marker.
- Other spellings ("Revert check", "revert evidence" in lower case). Only the exact `Revert evidence` prefix is skipped.
- Re-rendering the bodies of already-open or merged PRs.
- CLAUDE.md wording, a governing file that is the owner's.

## Acceptance Criteria
- AC1: a Test Summary line `- Revert evidence: with the fix reverted, 3 tests FAIL` gives no gap.
- AC2: `2 FAIL (pre-existing)` and `Known gap: x` lines are still gaps, each once.
- AC3: a ticket whose only `FAIL` line is revert evidence renders `KNOWN_GAPS_NONE_STATED`.
- AC4: the docstrings and the delivery_process.md paragraph state the skip.
- AC5: `.venv/bin/python -m pytest tests/tools/test_delivery_pr_render.py -q` passes. The run stays scoped to that file, not the full
  suite.

## Related Tickets
- TCK-20260927-PR-RENDER-CHECK-ALWAYS-DIFFERS, TCK-20260925-PR-RENDER-TABLE-CELL-NEWLINES (earlier pr_render fixes).

## Related Docs
- `docs/guides/delivery_process.md` ("Known gaps", the `pr_render.py` paragraph).

## Related Stored Artifacts
- None (hotfix).

## Related Code Areas
- `tools/delivery/pr_render.py`, `tests/tools/test_delivery_pr_render.py`.

## Assumptions / Open Questions
- Assumes revert-evidence lines start with exactly `Revert evidence`, which the five PRs above all use. If a line both starts
  `Revert evidence` and contains `Known gap:`, the skip wins. A closing agent puts a real gap on its own line.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
