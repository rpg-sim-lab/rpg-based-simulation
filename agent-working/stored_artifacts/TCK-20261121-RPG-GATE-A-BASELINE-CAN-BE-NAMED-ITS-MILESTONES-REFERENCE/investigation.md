---
status: historical
layer: testing
authority: P2
audience: agent
ticket_id: TCK-20261121-RPG-GATE-A-BASELINE-CAN-BE-NAMED-ITS-MILESTONES-REFERENCE
phase: done
date: 2026-11-21
tags: []
---

# investigation — TCK-20261121-RPG-GATE-A-BASELINE-CAN-BE-NAMED-ITS-MILESTONES-REFERENCE

Read from the code: resolve_references took the first of the milestone only; _ruling_problem checked {ref, date} only; v1 holds its ruling at top level, later versions in rebaseline.owner_ruling, so the lint reads both. Existing v2 ref "#715 6920465555" fixes the accepted shape.
