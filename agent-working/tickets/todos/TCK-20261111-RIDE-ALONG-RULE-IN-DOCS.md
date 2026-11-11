---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261111-RIDE-ALONG-RULE-IN-DOCS
phase: open
date: 2026-11-11
tags: [delivery]
---

# TCK-20261111-RIDE-ALONG-RULE-IN-DOCS

## Title
The ride-along rule is written into CLAUDE.md and the delivery guide's PR Lifecycle

## Status
OPEN

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Owner rule #715 6793205403 (2026-11-11): small no-code changes ride in the next PR on their track.
That covers doc wording, monitoring week close-outs and re-closes, and glossary, registry or
summary text, and each one still closes its own ticket. A PR stands alone only when it changes
`src/` behaviour, carries evidence, unblocks a waiting seat, or is the only open PR on its track.
The docs still carry only the narrower 11-07 rule. lead-planner-u24 found the gap, and
lead-planner checked it on 8b7c63d37.

The owner approved the exact CLAUDE.md text, and decided that an evidence PR may stand alone
(#715 6793254041). This hotfix rides the hook-split batch under the rule itself.

## Scope
Apply the text below **verbatim**. Do not reflow or reword it.

1. `CLAUDE.md`: replace the single line that starts "Every PR closes at least one completed
   ticket:" (line 387 on 8b7c63d37) with this one line:

```
Every PR closes at least one completed ticket. Ticket filings, seat-ticket notes and small no-code changes (doc wording, monitoring week close-outs and re-closes, glossary, registry or summary text) ride in the next PR on their track, each closing its own ticket; a PR stands alone only when it changes `src/` behaviour, carries evidence, unblocks a waiting seat, or is the only open PR on its track (full rule and exceptions: `docs/guides/delivery_process.md`, "PR Lifecycle").
```

2. `docs/guides/delivery_process.md`, "PR Lifecycle", in the **PR size** paragraph: change
   "Ticket\nfilings, evidence records and seat-ticket notes" to "Ticket filings and seat-ticket
   notes", keeping the paragraph's existing line wrapping style.
3. The same file: add this paragraph directly after the **PR size** paragraph:

```
**Ride-along (owner rule, 2026-11-11, #715 6793205403).** Small no-code changes ride in the next PR on their track instead of a PR of their own: doc wording, monitoring week close-outs and re-closes, and glossary, registry or summary text. Each still closes its own ticket. A PR stands alone only when it changes `src/` behaviour, carries evidence (a measurement or proof run the PR is for), unblocks a seat that is waiting on it, or is the only open PR on its track. Why: every merge costs a full CI run, an owner merge, and a REGISTRY resync for every other open PR.
```

## Out of Scope
- Any other CLAUDE.md line (each needs its own owner OK).
- Changing `pr_render.py` or any check.

## Acceptance Criteria
1. `git diff` of CLAUDE.md shows exactly one line replaced, byte-identical to the text above.
2. delivery_process.md carries the new paragraph and the edited PR size sentence.
3. Every test that pins CLAUDE.md or delivery_process.md text passes. Grep tests/ for "seat-ticket
   notes" and "evidence records" before you commit.

## Related Tickets
- TCK-20261107-EVERY-PR-CLOSES-A-TICKET (the 11-07 rule this widens)

## Related Docs
- CLAUDE.md, docs/guides/delivery_process.md ("PR Lifecycle")

## Related Stored Artifacts

## Related Code Areas
- tools/delivery/pr_render.py (unchanged)

## Assumptions / Open Questions
- The hand-orchestrated closure must record the governing edit as usual (governing_edits hook).

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
