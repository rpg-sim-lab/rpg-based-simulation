---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK
phase: done
artifact_type: plan
date: 2026-11-17
tags: []
---

# Plan: TCK-20261020-SUSPENDED-PROJECTS-ARE-NEVER-RESUMED-SLOT-LEAK (N10)

Approved by rpg-designer (ruling 5b726a2f) through rpg-planner.
1. Core: `ProjectEnd.SUSPENSION_EXPIRED`, `ProjectState.suspended_since`, `SUSPENSION_TTL_TICKS = 200`, `suspend_record(project, tick)`, `expire_suspended(projects, tick)`; `end_record` drops the clock (follows the L4 bar).
2. The three SUSPENDED writers use `suspend_record`; `resume_project` clears the clock; the near-death writer also clears the current ids (R2).
3. FIELD_RULES row (fill None); cognition_export attribute.
4. The expiry pass runs in the CALLERS through one helper `evaluate_strategic_intent_with_expiry` (designer ruling A); `evaluate_strategic_intent` keeps its name and body. A new static test pins that every production caller goes through the helper.
5. Arbiter guard: golden sha of `evaluate_project_switch` updated deliberately (lead testing-authority, #715 6941681673).
6. Docs: Bible 04 section 4, divergence 2.212 (Bounded), parity ledger STRAT-354, ProjectEnd docstring.
7. Own-job runs (HARD): fix arm, 3 gate worlds x s42 x 5000 ticks, spied + plain twin (6 processes); L1-L4 = 0, SUSPENSION_EXPIRED >= 1, twin match, PINNED, logging_errors 0, exceptions {}; reported: cap-tail rows (urban s42/s123 1000t, main vs N10), the s123 deaths.
8. S10 pre-push set: scoped unit run (incl. tests/architecture), the 26 slow scenario tests, import contract, code health, mypy on touched files.
