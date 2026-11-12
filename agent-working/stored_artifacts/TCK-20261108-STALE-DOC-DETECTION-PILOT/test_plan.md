---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-STALE-DOC-DETECTION-PILOT
artifact_type: test_plan
tags: [ai, documentation, governance]
---

# Test Plan: TCK-20261108-STALE-DOC-DETECTION-PILOT

## Tests
- `tests/tools/test_doc_drift.py` (detect section): evidence-newer ranked by lag and count, unresolved name with a rename shown, a name that exists in code is not flagged, plan lifecycle with the real status enum, excluded classes skipped, the run reads the pin and leaves the tree untouched (an uncommitted edit changes nothing), one `git log` pass for times and one for renames regardless of doc count, reviewed_by quiet and flagged again after an evidence change, jsonl output.
- No test names or targets a known stale doc.
- Full `tests/tools/` in a lead slot before the push.
