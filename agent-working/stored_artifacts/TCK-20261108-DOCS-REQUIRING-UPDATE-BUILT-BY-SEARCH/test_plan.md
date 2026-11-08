---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH
artifact_type: test_plan
tags: [ai, documentation, process-improvement]
---

# Test Plan: TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH

## Regression Surface
`check_docs_to_update_coverage` (Verify) and its Format 1 regex; the investigator and Document-Update prompts in `implement-ticket.js` (workflow-text pin tests).

## New Tests Required
`tests/tools/test_docs_search.py` (29 tests):
- AC 1 replay on committed minimal fixtures: #837 finds items 1, 2 (required) and 6; #786 finds the README; the #819 fixture excludes item 9 as `review-record` with its hits kept.
- AC 3: one test per exclusion class (archive, audit, registry, historical-status, review-record), an active plan is not excluded, and an F5 comment hit is returned.
- Classification: live guide is a candidate; parity_ledger hits carry `owner: parity-updater`; engine matrices are not normative; ranking puts a direct hit before an importer hit.
- Inputs: public symbols (non-underscore only), identifier shape, base-minus-head symbols become old terms, mechanism hits, regex and graph importers with the source named, graph fallback.
- F5: invariant comments and docstrings only, word-boundary keywords ("back/stack/track" do not hit), unparseable Python gives no hits.
- AC 4: candidate and excluded table rows never match the real `_DOCS_BULLET_RE`.
- Sources: a pinned git ref reads the docs at that ref, not the working tree (real `git init` repo); the CLI prints MARKER JSON.

## Proof Plan
Replay against real history: `python3 -m tools.gate_checks.docs_search_replay` (output recorded in the ticket).

## Scoped Pytest Commands
`pytest tests/tools/test_docs_search.py tests/tools/test_document_update_phase_wiring.py tests/tools/test_gate_cli.py -n 1`; full `tests/tools` once before push in a lead slot.

## Anti-Drift Test Guards
Replay fixtures are minimal subsets (cited lines plus one decoy per class); real-history counts come from the replay script and are not asserted.
