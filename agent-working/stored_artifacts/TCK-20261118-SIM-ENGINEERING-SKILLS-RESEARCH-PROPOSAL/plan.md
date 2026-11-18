---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL
artifact_type: plan
tags: [skills, simulation-quality, testing]
---

# Plan: simulation-engineering skills research and proposal

## Phases (stop after P4)
- P1 Audit first (local, cheap): inventory .claude/skills and .claude/agents against six gap areas (causal consistency, mechanism interaction, lifecycle, temporal scaling, emergence, V&V); map to Bible chapters, docs/engine, parity ledger, mechanism registry, tests; reuse the skill-catalog epic findings.
- P2 Historical defect set: batch one ask to rpg-designer with the six candidates; for each, record which existing control should have caught it and why not.
- P3 Research: NASA-STD-7009, Sargent V&V, property-based and model-based testing, metamorphic testing, agent-based-model verification literature, Anthropic Agent Skills authoring and eval guidance. Per method: applies / partly / not, plus the reusable workflow form (checklist, review rubric, or tool, not necessarily a skill).
- P4 Proposal: small architecture with trade-offs and rejected options (including "no new skill, extend existing agents/tools"); eval plan (arms with/without, historical tickets, critical findings caught, false positives, context overhead in tokens).
- Gate: send to the leads for owner approval. No pilot, no skill written before it.

## Constraints
Skills must not restate world rules; Bible and docs/engine stay authoritative. No heavy runs. Yield to RPG M1 Phase 1.

## Artifacts
research.md, coverage_audit.md, proposal.md under agent-working/stored_artifacts/<ticket>/ at close.
