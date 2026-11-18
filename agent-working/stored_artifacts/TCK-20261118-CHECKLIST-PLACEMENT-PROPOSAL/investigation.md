---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261118-CHECKLIST-PLACEMENT-PROPOSAL
artifact_type: investigation
tags: [skills, process-improvement]
---

# Investigation summary

Entry point for `proposal.md`. Findings: (1) of 374 tickets closed since 2026-10-19 (origin/main 169deedc0), 138 have any phase event and 236 have none; non-skipped phases: Plan 60, Review 28, Architecture-Verify 1 (0.27%). (2) The universal points are the ticket file, the working-log row and the PR body. (3) `architecture_reviewer_static.py` is not wired to CI. (4) Owner decision on #715 (2026-11-18): approve O2 (required ticket section), O3 (render into PR body, lint), O6 (CI scans when the time contract lands), O7 (property pilot, already routed), O5 (advisory line in planner PR reviews); not O4 or O8; the held eval stays parked; efficacy measured prospectively on defects first reported after 2026-11-18. Limits: phase events are self-reported; no retrospective efficacy replay is possible for defects 2, 4 and the latch.
