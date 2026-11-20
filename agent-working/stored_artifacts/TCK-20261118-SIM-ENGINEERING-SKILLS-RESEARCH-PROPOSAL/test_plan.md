---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL
artifact_type: test_plan
tags: [skills, simulation-quality, testing]
---

# Test plan

Added at close for the done-checker. This ticket changed no code, tests, agent or skill files, so there is no pytest scope. Verification was documentary:

- Frontmatter of the ticket and every artifact validated with `tools/validate_frontmatter.py`.
- Every source in `research.md` carries a READ / SNIPPET / MEMORY label; quoted claims come from READ rows only.
- Defect counts in `proposal.md` were reconciled with `defect_set.md` (6 relayed plus 4 extras; class and detection-stage counts re-added).
- The proposal's attach point (`architecture-reviewer.md` line 23) and the hypothesis-import claim were checked against the repo on 2026-11-18.

The behavioural test of the proposal is the eval defined in `proposal.md` §4 and filed as TCK-20261118-ARCH-REVIEWER-LIFECYCLE-TIME-CHECKLIST-EVAL; it has not run.
