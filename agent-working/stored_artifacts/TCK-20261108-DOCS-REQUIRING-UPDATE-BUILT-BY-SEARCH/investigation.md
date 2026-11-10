---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH
artifact_type: investigation
tags: [ai, documentation, process-improvement]
---

# Investigation: TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH

Design: origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2), F1/F5. Decisions are in plan.md (approved with five conditions by agent-working-planner).

## Current Behavior
- `.claude/agents/investigator.md` ("Docs Requiring Update", Format 1/Format 2) and the Investigate prompt in `.claude/workflows/implement-ticket.js` leave the list to judgment.
- `tools/gate_checks/done_checker_static.py::check_docs_to_update_coverage` parses only Format 1 bullets with `_DOCS_BULLET_RE` (`^-\s+\`(docs/...)\``); a table row never matches it.
- `docs/` has about 1,290 searchable text files at the #837 base (docs/ plus README.md, `.md .yaml .yml .html .txt .csv .json`).
- graphify-out/graph.json has `imports` and `imports_from` edges but is the main checkout's HEAD graph, not a pinned ref.

## Findings from the replays (real git, pinned SHAs)
- #837 (`531010a9a`, base `531010a9a^`): audit items 1 and 2 are normative docs with path hits; item 6 is an architecture philosophy doc with a path hit. All three found.
- #786 (`6d3f6235c`): README.md (item 5) is found by a path hit with and without the old term `promtail`.
- Item 9 (`import_linter_soak_review.md`) is not a hit on #837 or #786 (no path or term of either diff appears in it) and has `status: active`. The planner decided on 2026-11-08: add a `review-record` exclusion class (stem ends `_review`, `_report`, `_audit`) and check item 9 on a third fixture, the #819 diff (`61e984212`, which changes `codebase/structure/importlinter.toml`, cited at the doc's lines 140-162). #817 does not hit the doc (checked at its base).
- Symbols: the first run searched every public name and returned 84 required docs for three code paths because one-word names (`execute`, `entities`, `shutdown`) match prose. Searching only identifier-shaped names (underscore or two capitals) is a rule about shape, not a stoplist; it cut required to 12.
- `docs/`-prefixed changed paths are the PR's own docs; the replay drops them from the changed set (they are not code paths).

## Measured noise (docs_search_replay.py, recorded at implementation time)
| Replay | Code paths | required | candidate | candidate per path | excluded |
|---|---|---|---|---|---|
| #837 | 9 | 12 | 80 | 8.9 | 74 |
| #786 | 7 | 1 | 18 | 2.6 | 6 |
| #819 | 1 | 0 | 4 | 4.0 | 1 |
Plan basis: about 19-25 candidates per path before the symbol-shape rule. Nothing was tuned to the known items.

## Docs Requiring Update
None.

The doc-updater pointer (`docs/architecture/doc_updater_agent.md`) belongs to the sibling ticket in the same PR, and the delivery_process section belongs to the hand-close ticket; neither is required by this ticket's own diff.

## Review-record class: files it excludes under docs/ (14 at origin/main, listed so the cost is visible)
docs/ai/agent_infrastructure_audit.md; docs/ai/codex_posttool_adapter_exact_config_diff_for_review.md (matches `_review`; looks like a live proposal, a likely wrong exclusion); docs/assets/aseprite_licence_review.md; docs/assets/icon_key_set_review.md; docs/assets/icon_set_v2_review.md; docs/assets/sample_map/gap_report.md; docs/brainstorm/agent-working-design/ai_first_architecture_maturity_review.html; docs/plans/architecture/port_leak_audit.md; docs/plans/codebase_health/import_linter_soak_review.md; docs/plans/codebase_health/python_code_craft_gates_soak_review.md; docs/plans/codebase_health/python_code_craft_structure_soak_review.md; docs/plans/codebase_health/src_package_structure_audit.md; docs/plans/design_enhancement/performance_optimization/performance_optimization_conflict_approval_review.md; docs/plans/rpg_design_roadmap/rpg_direction_alignment_audit.md. Excluded entries keep their hits and reason in the output, so a wrongly excluded live doc stays visible.

## Risks and Open Questions
- Planned paths versus the real diff at Investigate time: the gate-time run uses the real diff.
- "required" is a normative-tier direct hit; the investigator confirms it states the changed fact.
- The `_for_review` file above may be a false exclusion; left as measured, reported to the planner.
