---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL
phase: open
date: 2026-11-18
tags: [skills, simulation-quality, testing]
---

# TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL

## Title
Research and propose domain-specific simulation-engineering skills (research + proposal only; nothing is built)

## Status
INPROGRESS

## Tier
standard

## Type
chore

## Priority
P3

## Request Summary
Owner request logged on #715 comment 6969095188, relayed by lead-planner: add skills for how agents reason about and verify simulations, alongside the programming skills. The recurring gaps are not coding problems: causal consistency, mechanism interactions, lifecycle modelling, temporal scaling, emergent behaviour, V&V. Candidate areas (mechanism design/review, cross-mechanism consistency, temporal reasoning, simulation verification) are a starting hypothesis, not a committed structure.

## Scope
1. Source-backed research (peer-reviewed, standards, official docs): NASA-STD-7009, Sargent V&V papers, model-based and property-based testing, Anthropic Agent Skills design and evaluation guidance. For each method: does it apply here, and how does it become a reusable agent workflow.
2. Coverage audit of what already covers these areas: .claude/skills, .claude/agents, Mechanics Bible, docs/engine, parity ledger, mechanism registry, tests. Name the real gaps only.
3. A SMALL proposed architecture with trade-offs, and an eval plan (with vs without each skill on historical tickets: critical findings caught, false positives, context overhead).
4. One batched consult with rpg-designer for the historical defect set (via lead-planner / lead-planner-u24).
Deliverable: stored artifact under agent-working/stored_artifacts/<this ticket>/ (research.md, coverage_audit.md, proposal.md with eval plan).

## Out of Scope
- Writing any skill, running any eval pilot, editing any agent or skill file (gated on owner approval via the leads after step 3).
- Duplicating world rules: the Bible and docs/engine stay authoritative; skills encode reasoning and verification method only.
- Proposing a skill merely because a topic looks complex.
- Heavy runs on this host.

## Acceptance Criteria
- Every research claim cites a source; each method is marked applies / partly / not, with the project-specific reason.
- The coverage audit maps each gap area to existing coverage with file references, and lists the real gaps.
- The proposal is small, states trade-offs and rejected alternatives, and does not restate rules from the Bible.
- The eval plan names the historical ticket set, metrics, arms, and the context-overhead measure; the defect set is confirmed or amended by rpg-designer.
- Work stops after the proposal; approval is requested via the leads.

## Related Tickets
- TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC (catalog, triggering, usage tracking: reused, not redone)
- TCK-20260810-SKILL-USAGE-RETRO-TRACKING, TCK-20260805-SKILL-USAGE-METRIC

## Related Docs
- docs/brainstorm/simulation-rule-taxonomy-evaluation-direction.md (soft/causal correctness)
- docs/mechanics/, docs/engine/, docs/parity_ledger/, registries/mechanisms.yaml

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20260804-SKILL-CATALOG-MODERNIZATION-EPIC/

## Related Code Areas
- .claude/skills/, .claude/agents/, tools/mechanism_registry/

## Assumptions / Open Questions
- Low-priority lane: yields to RPG M1 Phase 1 on contention.
- Historical defect candidates (to confirm with rpg-designer): night check on raw world_time (#953); resolve-blocker project re-created every 80 ticks; STALEMATE give-ups; stale failure reason; suspended project holding its slot forever (#954); births S9 vacuous newborn branch.
- The pending Phase 2 dispatch to agent-working-implementer in the handover is closed and stays paused.

## Implementation Notes
Plan: agent-working/staging_artifacts/TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL/plan.md

## Test Summary
n/a (research and proposal; no code).

## Files Changed
(filled at close)

## Completion Summary
(filled at close)
