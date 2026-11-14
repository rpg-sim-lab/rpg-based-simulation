---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261108-PROJECT-FACTS-PAGE-GENERATED
phase: done
date: 2026-11-08
tags: [ai, documentation, governance]
---

# TCK-20261108-PROJECT-FACTS-PAGE-GENERATED

## Title
Project numbers come from one stats tool and a generated facts page with a --check.

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Batch D, P2 of the plan (origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR), P2 and acceptance criterion 6). Owner approval #715 6720445592 ("approve full plan staged, J pilot only, yes to all three"); lead-planner finding 2026-11-08; owner dispatch of PR 1 in the agent-working-planner session 2026-11-08. Lands in PR 3. Hand-derived counts disagreed (layer edges 129/145/156/157; parity-ledger total 6,201 vs 2,300).

## Scope
1. `tools/project_stats.py --ref <sha>` prints the plan's P2 list: src lines and modules; test files and static test functions; tickets and merged PRs (dated); roles, subagents, hooks and skills; parity-ledger entries by status and priority; import contracts and baseline edges; metric families and alert rules.
2. It writes `docs/architecture/project_facts.md` and has `--check`, following `docs/performance/phase_inventory.md`'s generated-page pattern. The header gives the ref SHA and each count's counting rule (what, which paths, which parser), which settles the parity-ledger total.

## Out of Scope
- Editing other docs to cite the page (follow-up per domain).
- Wiring --check into CI (needs the CI owner; propose it in the ticket).

## Acceptance Criteria
1. Plan AC 6: `--check` fails when the page is stale (test), and the header carries the ref and the counting rules.
2. Two runs at the same ref give byte-identical output (test).
3. tests/tools/ passes in a lead slot.

## Related Tickets
- TCK-20261108-EPIC-DOCS-AS-REVIEW-SOURCE

## Related Docs
- origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2; plan content @ d1fa1263c, pushed at 3ce5747fd; reaches main with lead-planner's PR)
- docs/performance/phase_inventory.md

## Related Stored Artifacts
- none

## Related Code Areas
- tools/project_stats.py (new), docs/architecture/project_facts.md (new)

## Assumptions / Open Questions
- Settled 2026-11-14 by lead-planner (owner of docs/architecture/**): agent-working-implementer may write the generated page docs/architecture/project_facts.md, marked generated (not hand-edited); header = ref SHA plus each count's rule (what, which paths, which parser); `--check` follows the phase_inventory pattern. After it lands, lead reviews page content only through the tool.
- tools/project_stats.py matches no domain's owns: add it to agent-working's owns in registries/session_roles.yaml in the same PR (lead: no objection), regenerate .claude/agents and every derived view, and run the full tests/tools dir (chunked, lead slot), not a -k subset, before the push.
- Dispatch approved by the owner on #715 6875225978 (closes the docs-as-review-source epic: on close, move the whole folder with SEQUENCE.md to done/). Dispatched after TCK-20261114-ROLE-CARD-DECISION-CITATION-INDEX, one at a time.

## Implementation Notes
- Plan, investigation, test plan: `agent-working/stored_artifacts/TCK-20261108-PROJECT-FACTS-PAGE-GENERATED/`. Reviewed by agent-working-planner (approved with changes, 2026-11-14): `--check` regenerates at the page's own header ref and only notes when HEAD has moved; metric families by `ast` over `prometheus_client` constructors; alert rules by YAML parse; no `--format json`; merged PRs with first and last commit dates; no edit to `delivery_process.md`.
- `tools/project_stats.py` reads git objects at the ref only (`ls-tree`, `cat-file --batch`, `log --first-parent`): no working tree, network, timestamps or repo imports. `--write` writes `docs/architecture/project_facts.md` (lead-planner OK 2026-11-14 for the page and its generated marking).
- Parity ledger rule: 2,307 entries = items of the top-level lists of the nine `docs/parity_ledger/*.yaml` files. The plan's 6,201 is not reproducible as an entry count (see investigation.md).
- The first cut of the metric rule (Counter/Gauge only) found 0 families because `prometheus_collector.py` builds them with `GaugeMetricFamily` and `CounterMetricFamily`; the rule now includes the `*MetricFamily` forms and requires a name plus a documentation argument so `collections.Counter(...)` is not counted.
- `registries/session_roles.yaml`: `tools/project_stats.py` added to agent-working's owns; the six agent-working cards regenerated, `generate_agents --check` 0 drift.

## Test Summary
- `tests/tools/test_project_stats.py`: 10 tests on a fixture git repo (every counter, parametrized test counts once, conftest not a test file, counts come from the ref not the working tree, byte-identical runs, header carries the ref and every count has a rule, `--check` passes fresh / fails on a hand edit / fails when rules change / passes with a note after HEAD moves / reports a missing page, header or ref) and one on the real tree (the committed page matches the tool at its own ref; skipped with a reason only if that ref is not in the clone).
- Scoped: `test_session_cards.py`, `test_session_roster.py`, `test_session_agent_generator.py` (130 pass); ruff on the new files clean.
- Full `tests/tools` (chunked, lead slot): see the PR.

## Files Changed
- New: `tools/project_stats.py`, `docs/architecture/project_facts.md` (generated), `tests/tools/test_project_stats.py`.
- Changed: `registries/session_roles.yaml` (owns), the six `.claude/agents/session-agent-working-*.md` cards (regenerated), the docs-as-review-source epic folder moved to `done/`, this ticket and its artifacts.

## Completion Summary
`python3 tools/project_stats.py --write` produces `docs/architecture/project_facts.md` at a git ref, with each count's rule beside it; `--check` regenerates at the page's own ref and fails on a hand edit or a rule change. This closes the last child of TCK-20261108-EPIC-DOCS-AS-REVIEW-SOURCE.

Proposals (no code, owner or CI-owner decisions): wire `python3 tools/project_stats.py --check` into CI (the real-tree test already runs it where the ref is in the clone); the weekly close (`make agent-monitoring-close-week`) runs `--write` and commits the page so the page ref follows main.

Known gap: other docs, CV rows and reviews do not cite the page yet; each domain does that as its own follow-up.
Known gap: the page counts 26 metric families by `ast` over `prometheus_client` constructors, while `docs/observability/prometheus_metrics.md` lists 13 `sim_` rows; the two disagree and the doc is not edited here.
Known gap: the page is as of its ref; it does not move until someone runs `--write`.
