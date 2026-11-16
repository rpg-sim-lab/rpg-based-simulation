---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261116-DOC-CITATION-RESOLVER-REPORT-ONLY
phase: open
date: 2026-11-16
tags: [ai, governance, testing]
---

# TCK-20261116-DOC-CITATION-RESOLVER-REPORT-ONLY

## Title
A report-only resolver checks that every backticked citation in the authoritative documents names a file and symbol that exist.

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P3

## Request Summary
Amended 2026-11-16 for the owner's agent-practice decision 2A (#715 6913007039): scope item 5 and AC5 add comment and docstring pointers.

Docs-truth track of the SDLC plan (`docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md`, "Docs-truth track" under Phase 4). Filed by agent-working-planner on 2026-11-16 from agent-working-designer's hand-off. The owner's decisions are on #715: 6911224913 (Q3: all four checks start report-only, none blocking) and 6911534263. The measurements and reasoning are in `agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md`. Filing only: dispatch needs a separate owner go. P3, behind RPG work (#715 6911759453). 

## Scope
1. **Controls come first in the tests.** This designer's own name-matching check failed exactly these controls: it reported `WorldState`, `AdventureDecisionPhase` and `process_active_contracts` missing, and all three exist.
   - Positive control: a fixture citing a removed symbol is flagged.
   - Negative control: a fixture citing a nested function, a decorated function and a dataclass field, all present, is not flagged.
2. **An AST-based resolver.** It covers every backticked citation in the authoritative documents: `docs/mechanics/`, `docs/engine/`, `docs/parity_ledger/`, `docs/guidelines/intentional_divergences.md` and `docs/world_rules/`.
   - It checks that the file exists, and that a cited function, class, flag or test node id is defined in it.
   - A `file:line` citation is accepted next to a symbol, and only the symbol is checked.
   - It parses `def` and `class` properly, not by regex.
3. **Report-only.** One line per unresolved citation, with counts per document. Run it as a non-failing CI step.
4. **Baseline.** Record the path-existence rates per area at the commit it is built on (designer's figures at db6b4579d: 5.4% overall, mechanics 1.4%, world_rules 0.5%, engine 5.8% excluding the knowledge-gateway set).

5. **Comment and docstring pointers** (owner #715 6913007039, point 2A: "check comment pointers for dead paths"). Extend the resolver to comments and docstrings in `src/` and `tools/` (Python, using `tokenize` and `ast`).
   - For every repo-path or `path::symbol` citation, report whether the path exists and the symbol is defined.
   - The rules and the report-only output are the same as for documents. A line number beside a symbol is accepted, and only the symbol is checked.
   - Baseline to record at the build commit: at db6b4579d, 302 comment pointers cite a repo path, and 9 of them are dead (3.0%), per agent-working-designer.

## Out of Scope
- Blocking CI; rewriting any document; line-number resolution.
- Removing or rewriting any comment. Under the owner's 2A, narration is removed only on lines a ticket already touches. In `src/` that is rpg's call, sequenced around M1; in `tools/` it is agent-working's call, by the same rule.

## Acceptance Criteria
1. Both controls pass in the tests and are the first tests in the file.
2. The resolver runs over the authoritative set and reports per document, never failing the run on a finding.
3. The baseline per area is recorded in the Test Summary, at a named commit.
4. A CI step runs it report-only. The workflow-file edit is a governing change: the exact diff goes to the owner through lead-planner before commit.
5. The comment scanner's first tests are its own controls, in the same order as the document controls. Positive: a comment citing a removed path is flagged. Negative: a comment citing an existing file and a nested function is not.

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261116-THIRTEEN-DEAD-KNOWLEDGE-GATEWAY-DOCS-MOVE-TO-THE-ARCHIVE (removes most of engine's dead paths)

## Related Docs
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md (Docs-truth track)
- agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md

## Related Stored Artifacts
- agent-working/stored_artifacts/sdlc-decisions/docs_truth_plan.md

## Related Code Areas
- tools/gate_checks/ (new resolver; doc_drift.py and docs_search.py are related)
- .github/workflows/test.yml

## Assumptions / Open Questions
- Paths to generated or untracked files read as dead. List them as a known class rather than suppressing them.

## Implementation Notes
(to be filled by the implementer)

## Test Summary
(to be filled by the implementer)

## Files Changed
(to be filled by the implementer)

## Completion Summary
(to be filled by the implementer)
