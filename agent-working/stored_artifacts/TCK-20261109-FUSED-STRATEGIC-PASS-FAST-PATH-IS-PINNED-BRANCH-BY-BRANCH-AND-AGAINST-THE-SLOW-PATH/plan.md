---
status: historical
layer: testing
authority: P2
audience: agent
artifact_type: plan
ticket_id: TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH
phase: done
date: 2026-11-09
tags: [testing]
---

# TCK-20261109-FUSED-STRATEGIC-PASS-FAST-PATH-IS-PINNED-BRANCH-BY-BRANCH-AND-AGAINST-THE-SLOW-PATH: plan

Test-only. One new file under tests/unit/strategic/ (rpg-planner's tests route; rpg-planner signs off): characterisation rows 1-7 plus the inactive/dead skip, and a 13-row fast-against-slow differential with a known-disagreement table (row 1 strict xfail citing defect A; row 6 pinned as different citing CLEAR-TARGET). State is hand-built, nothing mocked. No src change. Proof of each row: a one-line perturbation of the source in the worktree turns it red, recorded in the ticket, nothing under src committed.
