---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261123-STATE-DIGEST-PROBE-SET-PERTURBATION-MUST-CHANGE-THE-SET
phase: done
date: 2026-11-24
tags: []
---

# investigation - TCK-20261123-STATE-DIGEST-PROBE-SET-PERTURBATION-MUST-CHANGE-THE-SET

synthesize returns the first enum member (and 1 for int), already held by the synthesized or live set, so the union equals the original. A Set[int] like state.groups[].member_ids collides the same way.
