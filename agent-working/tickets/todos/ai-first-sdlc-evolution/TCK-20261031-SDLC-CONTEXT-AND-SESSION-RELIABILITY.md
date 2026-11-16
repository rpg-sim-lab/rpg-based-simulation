---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY
phase: open
date: 2026-10-31
tags: [ai, governance, delivery]
---

# TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY

## Title
Agents can trust the freshness and authority of search, graph and handover context.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Phase 5 (plan section 39). It needs no owner decision, is independent of the other phases, and can run in parallel.

Owner decision 2026-11-15 (#715 6889309909, 6889318166): this is the epic's next ticket, dispatched to the agent-working seats after the ticket view epic (P3c and the backlog view) lands.

## Scope
1. ~~Fix the search staleness root; the stale flag is correct in worktrees.~~ Split out on 2026-11-15 as TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT, the owner's vehicle for the native implement-ticket run (#715 6889489078).
2. Add an authority field and history down-weighting.
3. Mark branch content as not indexed.
4. Rebuild the graph on a schedule and print its build SHA.
5. A handover header and a write-time cap.
6. A canonical session path to fix the memory split.
7. Provenance labels on injected content.
8. Run E3 (plan section 45) and report.

## Out of Scope
- Search engine replacement.
- Editing the user's memory content.
- Thresholds the plan leaves to the owner: propose after the baseline; do not set them.

## Acceptance Criteria
1. ~~The stale flag is correct in worktrees, with a test.~~ Moved to TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT.
2. E3 baseline and after-numbers are recorded over 20 authority queries; the owner sets the share.
3. No handover over the cap without a write-time warning.
4. `tests/tools/` passes in a lead slot.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_DECISION_SUMMARY.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/knowledge_search.py, tools/search_mcp.py, tools/hybrid_retrieval.py
- tools/sessions/session_start_hook.py, tools/graphify_*

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details from either host stay out of committed files, tickets and public comments unless a decision needs them; they go to the owner directly.
- No credential or ruleset change is authorised by the epic; each gets its own owner ask, by ticket.
- Undecided, and not to be written as decided: OD-4 to OD-9, OD-11 to OD-13, OD-16 to OD-21.
- Recheck against main 0f1c35206 (agent-working-planner, 2026-11-15), before dispatch. Scope items as filed:
  1. **Still open, live.** TCK-20261112-SEARCH-SERVER-PER-WORKTREE-INDEX-AND-BUILD-MEMORY-GUARD (#888) made worktree sessions read the main checkout's index. But `tools/knowledge_search.py::index_staleness` still compares the manifest's mtimes against this checkout's root, so a worktree reports a stale index that isn't. Evidence: `search_docs` in the agent-working-planner worktree on 2026-11-15 returned `stale: {changed: 5683, new: 30, removed: 0}`. The fix compares against the corpus root the index was built from.
  2. **Partly there.** `tools/hybrid_retrieval.py` already resolves authority and freshness from the registry, as an opt-in pre-fusion filter. `search_docs` doesn't use it, and there is no history down-weighting.
  3. **Partly overtaken by #888.** Worktree sessions read main's index, so branch content is not indexed by construction, but nothing tells the reader so.
  4. **Open.** The worktree link to the shared graph exists (`tools/graphify_link.py`, #506) and so does pruning. There is no scheduled rebuild, and no build SHA is printed.
  5. **Open as filed.** `tools/sessions/session_start_hook.py` cuts a note over `HANDOVER_CAP_CHARS` (8000) and warns at read time. There is no header and no write-time warning.
  6. **Open, and on both hosts.** On ubuntu, auto-memory has two directories, one for each spelling of the path (`/home/vboxuser/Work` is a symlink to `/data/vboxuser/Work`). The audit found the same split on u24.
  7. **Open.** No provenance label or size cap on injected content was found, beyond the harness's own wrapper on cross-session messages.
  8. **Not started.** E3 has not run.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
