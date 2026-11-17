---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-READ-COUNTER-FOR-PROCESS-DOCUMENTS
phase: open
date: 2026-11-16
tags: [ai, agent-monitoring, process-improvement]
---

# TCK-20261116-READ-COUNTER-FOR-PROCESS-DOCUMENTS

## Title
Read rows record what kind of file was read, from the full path, so a 2-4 week report can show which process documents other sessions actually read.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Filed by agent-working-planner on 2026-11-16 from agent-working-designer's hand-off, for the owner's agent-practice decision 3A (#715 6913007039): "A: count reads first (Recommended)". The decision is to cut nothing yet: add a read counter for 2-4 weeks, then decide from the numbers. Authoritative documents and decision records are kept regardless.

Why a counter is needed: tool rows cut `input_summary` at 120 characters (`tools/agent-monitoring/post_tool_hook.py::_input_summary`), so a read of a long stored-artifact path often can't be attributed. The designer's count gives only a floor: 21 reads against 142 writes, on the rows whose path survived the cut. A citation count failed as a read measure.

Evidence: `agent-working/stored_artifacts/sdlc-decisions/agent_practice_options.md`. Filing only: dispatch needs a separate owner go. P3, behind RPG (#715 6911759453).

## Scope
1. **Two optional fields, on Read rows only.**
   - `read_path_class`: one of `stored_artifact`, `staging_artifact`, `ticket`, `doc`, `code`, `other`.
   - `read_path_id`: the ticket-id directory for artifacts, else null.
   - Both are computed from the full `file_path`, before the 120-character cut.
   - The full path is never stored, and the redactor still runs over any string that reaches the row.
   - The hook registration in `.claude/settings.json` doesn't change, so this is not a governing edit.
   - Readers tolerate rows without the fields.
2. **Schema.** Document the fields in `docs/agent-monitoring/schema.md`.
3. **A read-only report** in `tools/agent-monitoring/`, over N weeks of shards. It gives:
   - reads per class;
   - for artifacts, reads by a session other than the one that wrote the artifact, and reads in a later week than the write;
   - the share of artifact directories read at least once.

   It keeps re-reads by the same session apart from reads by another session, because only the second shows a document being used.
4. **After the window.** Once 2-4 weeks of data exist, run the report and store the result for the owner. This ticket cuts no document.

## Out of Scope
- Bash `cat` and `grep` reads: a known undercount, to be named in the report.
- `search_docs` hits: the MCP tool doesn't log them. Say so in the report.
- Deleting or moving any document.
- The close rule or `done_checker`.

## Acceptance Criteria
1. Controls, in tests:
   - a Read of a 200-character artifact path is classed correctly (the old cut would have lost it);
   - a Read of an unrelated file gets class `other`;
   - a row without the new fields is read without error.
2. The report runs on the existing shards with the fields absent, and says how many rows it couldn't classify.
3. After the window, the owner has a read share per class, with its undercounts stated, in a stored artifact.
4. A test shows that no full path or secret-shaped string reaches the new fields.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261116-SDLC-ATTRIBUTION-FIELDS-AND-COORDINATION-METRICS (also adds tool-row fields; coordinate the schema edits)

## Related Docs
- docs/agent-monitoring/schema.md
- agent-working/stored_artifacts/sdlc-decisions/agent_practice_options.md

## Related Stored Artifacts
- agent-working/stored_artifacts/sdlc-decisions/agent_practice_options.md

## Related Code Areas
- tools/agent-monitoring/post_tool_hook.py (`_input_summary`)
- tools/agent-monitoring/ (new report)

## Assumptions / Open Questions
- The 120-character cut itself is a documented limit, and this ticket doesn't change it.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
