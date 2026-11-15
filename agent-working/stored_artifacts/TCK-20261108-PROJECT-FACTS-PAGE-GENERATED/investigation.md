---
status: active
layer: ai
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20261108-PROJECT-FACTS-PAGE-GENERATED
phase: done
date: 2026-11-14
tags: [ai, documentation, governance]
---

# Investigation: one stats tool and a generated project facts page

Read at origin/main 6822509a8. Plan: `agent-working/lead/docs_as_review_source_plan.md` P2 and AC 6. Pattern: `tools/perf/phase_inventory.py` (+ `docs/performance/phase_inventory.md`, `tests/tools/test_perf_inventories_committed_in_sync.py`).

## What exists
- **Generated-page pattern.** `phase_inventory.py` parses source with `ast`, never imports engine code, prints no timestamps, has `--format md|json` and `--check <committed json>`; a test runs the tool's `--check` against the committed file and a second test proves a drifted value fails it. Its md header says "Generated from commit <sha> by <tool>. Regenerate with: ...".
- **Counts and where each comes from (measured today, indicative only):**
  - src lines and modules: `*.py` under `src/` at the ref.
  - test files and static test functions: `tests/**/test_*.py` and `ast` `def test_*` (parametrized cases are not expanded: say so).
  - tickets: files under `agent-working/tickets/{todos,inprogress,done}`; merged PRs: first-parent commits on the ref whose subject ends `(#N)` (squash merges), dated by the ref commit. Needs git only, no network, so it is byte-stable for a given ref.
  - roles (`registries/session_roles.yaml`), subagents (`.claude/agents/*.md` not starting `session-`: 16; the `session-*` cards counted separately), skills (`.claude/skills/*`: 23), hooks (`.claude/settings.json` `hooks`: 18 entries in 7 events).
  - parity-ledger entries: the lists in `docs/parity_ledger/*.yaml` (schema.json and README excluded). A YAML parse of the top-level lists gives **2,307** entries across 9 ledgers; the 6,201 in the plan's table is not reproducible as an entry count (it looks like a line or key count). The page states the rule and the status x priority table.
  - import contracts and baseline edges: 17 `[[...contracts]]` blocks in `codebase/structure/importlinter.toml`; 129 non-comment lines in `codebase/structure/import_layers_baseline.txt` (each is one baseline edge).
  - metric families: `sim_*` names in `src/observability/prometheus_collector.py` (47 distinct strings today, but metric type declarations need confirming); alert rules: rules in `docker/grafana/provisioning/alerting/rules-*.yaml` (to count by `uid:`).
- `tools/project_stats.py` matches no domain's owns (`registries/session_roles.yaml`): must be added to agent-working's owns in the same PR; the cards then change and need regenerating.

## Findings that shape the design
1. **Read from the ref, not the working tree**, so two runs at one ref are byte-identical and `--check` can run on any checkout: `git ls-tree`/`git cat-file --batch` for the ref. `--ref` default = `HEAD`.
2. **`--check` compares to the committed page at the page's own ref**, not at HEAD, otherwise it is stale on every commit and fails each PR (the problem the phase inventory solved by ignoring the embedded commit id). Proposal: the page header records the ref SHA; `--check` regenerates at the header's ref and compares bytes, and a separate informational line says how far HEAD has moved. This means the page goes stale only if the tool or its rules change, not when code grows. Staleness at HEAD is reported as a note, not a failure (counts "as of ref").
3. The merged-PR count is the only count that is date-sensitive; it is taken from the ref's history, so it is stable per ref.

## Open questions
1. Is "check at the header's ref" right, or should `--check` fail when the page's ref is older than N commits? (Plan AC6 only requires failure when the page is stale.)
2. Metric families and alert rules: confirm the two counting sources above with the observability owner (lead-planner owns docs/architecture; metrics are rpg/platform). I will state the rule in the page either way.
3. Do you want the tool's JSON output too (`--format json`) for the weekly close script?

## Review outcome (agent-working-planner, 2026-11-14) and what changed
- Q1: `--check` regenerates at the page header's own ref and compares bytes; HEAD past that ref prints a note, never a failure. The Completion Summary proposes who refreshes the page (the weekly close running `--write`) next to the CI wiring proposal.
- Q2: metric families are counted by `ast` as `prometheus_client` constructor calls with a literal name and a documentation argument, deduped by name (not by a `sim_` prefix in one file); constructors are Counter, Gauge, Histogram, Summary, Info and their `*MetricFamily` forms, because `prometheus_collector.py` builds its families with `GaugeMetricFamily` and `CounterMetricFamily` (a first-cut Counter/Gauge-only rule found 0 there). `collections.Counter(...)` takes one argument and is not counted. Alert rules are `groups[].rules[]` of `rules-*.yaml` parsed as YAML (11 today).
- Q3: no `--format json`. The `delivery_process.md` sentence is dropped (per-domain follow-up, listed in the Completion Summary).
- Merged PRs print the count with the first and last commit dates at the ref.
- **Parity 6,201:** not reproducible as an entry count. At 6822509a8 the nine ledgers hold 2,307 entries (`- id:` lines = `status:` lines = `priority:` lines = 2,307); the files hold 39,655 lines and 11,517 lines carrying one of `status|priority|proof_type|test_path|v2_evidence`; no combination of per-entry keys gives 6,201 (3 x 2,307 = 6,921 is the nearest). The old figure most likely came from a different count (a key or line count over an earlier tree), which cannot be recovered; the page's rule (list items) is the one that makes the number stable.
