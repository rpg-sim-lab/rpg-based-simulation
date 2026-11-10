---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY
artifact_type: plan
tags: [ai, documentation, process-improvement]
---

# Plan: TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY

Design source: origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2, content @ d1fa1263c), "Owner correction" F2/F3, R3, acceptance criteria 1 and 4. Cited, not copied. Depends on TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH (the shared search); built after it in the same PR.

## F2: doc-updater
- `.claude/agents/doc-updater.md` Step 0 and "What to Do": after the required docs, a **satellite step**. The orchestrator injects the three lists from the shared search run on the real diff. For each `candidate`: edit the doc if it restates the changed fact, otherwise report it in `docs_skipped` with a reason. "Never derive yourself" is lifted for candidates only.
- Rules, in the agent file: explanatory docs only; a normative doc changes only when the ticket itself changes intended behaviour and cites the rule owner's approval, otherwise the disagreement is reported as a defect or a divergence; excluded (history) docs are never edited; a defect is never written into a normative doc as if intended (plan AC 4); `parity_ledger/` candidates are left to parity-updater.
- The rules are stated once in doc-updater.md. `docs/architecture/doc_updater_agent.md` gets a pointer, not a copy.

## Wiring
`implement-ticket.js` Document-Update (:1211-1273): the orchestrator runs the shared CLI with `files_changed` (real diff, same source the staleness gate uses) and passes required/candidate/excluded into the prompt. `DOC_UPDATE_SCHEMA` is unchanged: skips already go in `docs_skipped`. A search failure is reported in the prompt ("search unavailable") and never fails the phase.

## F3: advisory in doc_staleness_check.py
`check_doc_staleness` gains an optional `search_result` argument; when given, it appends one `ADVISORY` entry listing docs that cite a changed src file or symbol and are not in `files_changed`, minus the excluded list. The existing PASS/FAIL logic and exit behaviour are untouched; the advisory is appended only after the verdict. Ordering: docs on a critical invariant (determinism, conservation, persistence and restore, concurrency, message acknowledgement, plan P5) first, matched by a fixed keyword list on the path and the hit text; those are named in the evidence string so the close summary can quote them. The gate CLI gets an optional `--search-json` flag; absent, behaviour is byte-identical to today.

## Tests
See test_plan.md. Open questions: none beyond TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH's question 1 (the item-9 fixture), which this ticket's criterion 1 reuses.

## Deviation from the ticket text (accepted by agent-working-planner, 2026-11-08)
The ticket says the orchestrator passes the lists into the Document-Update prompt. Instead the prompt carries a ready command, `python3 tools/gate_checks/docs_search.py --start-sha <start sha>`, and doc-updater runs it. Reason: injecting lists needs a new attested gate site (a `gateCmd` key, a `gate_cli.py` sub-command, the gate-policy extractor and their pinned bounds); a command in the prompt needs none. Conditions kept: (a) `--start-sha` derives the changed files with `gate_checks/changed_files.py::derive_changed_files`, the function the staleness gate uses, so doc-updater never computes its own diff; (b) a failed search prints an `error` marker and exits 0, and doc-updater reports it in `docs_skipped`/`verified_by` and keeps going; the phase never blocks; (c) this record.
