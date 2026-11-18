---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261118-SIM-ENGINEERING-SKILLS-RESEARCH-PROPOSAL
artifact_type: investigation
tags: [skills, simulation-quality, testing]
---

# Investigation summary

Added at close: the done-checker requires an `investigation.md` for a standard-tier ticket. The investigation itself was written under task-specific names; this file is the entry point and states the conclusions. Detail lives in the files named.

## Findings
1. Existing coverage already holds the rule truth (Bible, engine, world_rules), mechanism reachability (registry `verified` axis), test technique criteria (`test_taxonomy.md` §6) and structural guards (`tests/architecture/`). The gap is an operational check at review time. Detail: `coverage_audit.md`.
2. `hypothesis` is a declared dependency but no file imports it (checked 2026-11-18).
3. Domain skills were almost never invoked and only binding gates worked (skill-catalog epic investigation, 2026-08 figures). Delivery form decides outcomes.
4. Applicable methods: traces, degenerate and extreme-condition tests, stateful property tests; partly: verification/validation split and "record what is not verified". Not now: metamorphic testing, NASA credibility scoring, ODD. Detail and read-status of each source: `research.md`.
5. Ten historical defects (rpg-designer via the leads, 2026-11-18): by my count 5 lifecycle, 2 time/scale, 2 cross-layer, 1 measurement design. Detail: `defect_set.md`.
6. Recommended and owner-approved option: a concrete lifecycle and time checklist in `architecture-reviewer`, adopted only if a small eval passes. Detail: `proposal.md`.

## Limits
Metamorphic-testing surveys and ODD were read from search snippets only; QuickCheck from memory. Defect labels were relayed, not checked against git (follow-up ticket does this).
