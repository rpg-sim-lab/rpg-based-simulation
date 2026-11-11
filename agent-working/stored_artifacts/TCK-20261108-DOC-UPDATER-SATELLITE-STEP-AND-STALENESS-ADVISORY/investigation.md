---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY
artifact_type: investigation
tags: [ai, documentation, process-improvement]
---

# Investigation: TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY

Design: origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2), F2/F3. The shared search and its replay findings are in the sibling ticket's investigation.md (define once).

## Current Behavior
- `.claude/agents/doc-updater.md` Step 0: input is only Investigate's list ("never something you derive yourself").
- `implement-ticket.js` Document-Update (about :1211-1273) passes the list; the doc-staleness gate (`doc_staleness_check.check_doc_staleness`, run through `gate_cli.py doc_staleness --start-sha`) derives changed files from git and appends an ADVISORY only for `docs_to_update` paths that were not touched.
- `gate_cli.py`'s commands are bounded (GATE_CMD_BOUND) and each gate site is registered in `gate_policy_extractor`; a new attested site would touch both.
- The JS read only the first ADVISORY row.

## Decisions
- The search command is placed in the Document-Update prompt and doc-updater runs it (it has Bash); no new attested gate site. The advisory runs orchestrator-side inside the existing `doc_staleness` site and is best effort (a failing search returns None and the output stays byte-identical).
- The JS now joins all ADVISORY rows into the event summary.
- `docs/architecture/doc_updater_agent.md` gets a pointer; the rules live once in doc-updater.md.

## Docs Requiring Update
- `docs/architecture/doc_updater_agent.md`: pointer to the satellite step.

## Risks and Open Questions
- The F2 rules are prompt text; their effect is judged on the first runs, not by a test. The tests pin the text and the gate behaviour.
