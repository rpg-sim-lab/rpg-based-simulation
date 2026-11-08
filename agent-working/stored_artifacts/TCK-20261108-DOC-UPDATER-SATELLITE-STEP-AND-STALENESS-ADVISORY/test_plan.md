---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY
artifact_type: test_plan
tags: [ai, documentation, process-improvement]
---

# Test Plan: TCK-20261108-DOC-UPDATER-SATELLITE-STEP-AND-STALENESS-ADVISORY

## Regression Surface
`check_doc_staleness` verdicts and CLI output; `gate_cli.py doc_staleness`; the Document-Update phase wiring tests.

## New Tests Required
`tests/tools/test_doc_staleness_search_advisory.py` (14 tests):
- The advisory lists untouched live docs and keeps the PASS verdict; a touched doc is not listed; excluded docs never appear; item 9 is marked excluded in the input and never listed (AC 1).
- Critical-invariant docs come first and are named; the keyword match is on word boundaries (AC 3).
- A missing or malformed `search_result`, and a search failure in `gate_cli`, leave the output byte-identical; a FAIL verdict is never changed (AC 2).
- doc-updater.md carries the satellite step with every rule; the Document-Update prompt carries the search command; the JS shows every ADVISORY row; the investigator is told to build the list by search.

## Proof Plan
AC 1 end to end is the replay in the sibling ticket plus the tests above.

## Scoped Pytest Commands
`pytest tests/tools/test_doc_staleness_search_advisory.py tests/tools/test_doc_staleness_gate_wiring.py tests/tools/test_document_update_phase_wiring.py tests/tools/test_gate_cli.py -n 1`; full `tests/tools` once before push in a lead slot.

## Anti-Drift Test Guards
Text pins use the rule sentences that matter, not whole paragraphs.
