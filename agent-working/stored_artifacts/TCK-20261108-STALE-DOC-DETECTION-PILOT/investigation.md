---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-STALE-DOC-DETECTION-PILOT
artifact_type: investigation
tags: [ai, documentation, governance]
---

# Investigation: TCK-20261108-STALE-DOC-DETECTION-PILOT

## Findings
- First measured run at 5c6990e51: 20 s, 88 MB, 599 live docs of 1,182 read, 480 flagged (80%): evidence-newer 354, unresolved-name 333, plan-lifecycle 72.
- Labelled recall at 531010a9a: items 1 and 6 flagged with the plan's own counts (14 of 21 and 9 of 17 paths newer); item 2 flagged only by unrelated unresolved names, so not credited; item 4 not flagged. Measured and reported, not tuned.
- Hand-read sample of 20: 8 true positives, 10 false, 2 unclear (50% false, 60% if unclear counts false). plan-lifecycle was the most precise.
- A first draft of the report used the wrong denominator (all docs read, not live docs); `detect` now returns `live_docs`.
