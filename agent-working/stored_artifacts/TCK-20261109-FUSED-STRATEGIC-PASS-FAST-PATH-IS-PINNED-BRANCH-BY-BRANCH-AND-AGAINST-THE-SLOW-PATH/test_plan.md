---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: test_plan
ticket_id: TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH
phase: done
date: 2026-11-09
tags: [testing]
---

# TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH: test_plan

## Proof Plan
- level: unit
- proof kind: characterisation (Feathers) plus a fast-against-slow differential on the same entity state
- oracle source: the current behaviour of the code, not a document; the differential's equal rows are the agreement the two paths are meant to have
- expected effect: any change to a pinned branch of the fast path, or a new fast/slow disagreement, turns a test red
- selected commands: pytest tests/unit/strategic/test_fused_strategic_pass_fast_path_characterisation.py
