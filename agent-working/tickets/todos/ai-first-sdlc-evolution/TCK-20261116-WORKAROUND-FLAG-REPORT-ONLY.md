---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-WORKAROUND-FLAG-REPORT-ONLY
phase: open
date: 2026-11-16
tags: [ai, governance, process-improvement]
---

# TCK-20261116-WORKAROUND-FLAG-REPORT-ONLY

## Title
A report-only check flags added comments that say TODO, HACK, workaround or "for now" without a ticket id.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Filed by agent-working-planner on 2026-11-16 from agent-working-designer's hand-off, for the owner's agent-practice decision 1A (#715 6913007039). As lead-planner recorded it: "A: ticket id + report-only flag (Recommended)". The decision is scoped to correctness and hard-rule fixes, not balance tuning. A workaround or "temporary" fix must name its root cause and carry a ticket id, with the reason in the ticket rather than in an apology comment. A report-only close-check line flags TODO, HACK, workaround or "for now" in added lines that have no `TCK-` id.

Evidence and options: `agent-working/stored_artifacts/sdlc-decisions/agent_practice_options.md`. Filing only: dispatch needs a separate owner go. P3, behind RPG (#715 6911759453).

## Scope
1. **Controls come first in the tests.**
   - Positive: an added `# workaround for X` with no ticket id is flagged.
   - Negative: the same comment carrying `TCK-20261116-EXAMPLE` is not flagged.
   - Negative: a variable named `temporary_dir` is not flagged, and neither is the word inside a string.
2. **A function that reads a PR's added lines.** It reports each comment containing `TODO`, `HACK`, `FIXME`, `XXX`, `workaround`, `work-around`, `temporary`, `temporarily`, `for now` or `kludge` (whole words, case-insensitive) that has no `TCK-\d{8}` id in the same comment block.
   - Comments are found with `tokenize` for Python, and with a `//`, `/* */` or `#` rule for the repo's other languages.
   - Code identifiers and string literals never match.
3. **Output.**
   - One line per finding in the close check's step summary, once TCK-20261116-SDLC-CLOSE-CHECK-REPORT-ONLY-GATE-JOB exists.
   - Until then, it runs as a report-only condition of `tools/gate_checks/done_checker_static.py --ticket-id` that never changes the exit code.
4. **No judgement.** The tool doesn't decide whether a finding is a correctness or hard-rule workaround or something else, such as a balance-tuning note. A person judges that.
5. **Baseline.** Run it read-only over the last 50 merged PRs, and record per PR the count and which findings were false positives. agent-working-designer's measurement at db6b4579d: of 13,758 Python `#` comments in `src/` and `tools/`, only 25 match these words, and 3 of those carry a ticket id.

## Out of Scope
- Blocking; judging whether a fix is "proper"; removed or unchanged lines; changing the ticket template.

## Acceptance Criteria
1. The controls pass and are the first tests in the file.
2. The 50-PR baseline is recorded, with the false positives named.
3. The line appears for a PR, or a done_checker run, that adds a flagged comment, and it never fails a run.
4. If the close-check job's workflow file is edited, that is a governing change: the exact diff goes to the owner through lead-planner first.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261116-SDLC-CLOSE-CHECK-REPORT-ONLY-GATE-JOB (the step-summary line depends on it; the function doesn't)

## Related Docs
- agent-working/stored_artifacts/sdlc-decisions/agent_practice_options.md

## Related Stored Artifacts
- agent-working/stored_artifacts/sdlc-decisions/agent_practice_options.md

## Related Code Areas
- tools/gate_checks/done_checker_static.py
- tools/gate_checks/ (new function)

## Assumptions / Open Questions
- Proposed, not owner-decided: bug tickets would state which layer holds the root cause (producer or consumer). That changes the ticket format in CLAUDE.md, so it needs the owner's direct yes. It is not part of this ticket.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
