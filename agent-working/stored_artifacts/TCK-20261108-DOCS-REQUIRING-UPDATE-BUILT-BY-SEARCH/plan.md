---
status: active
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH
artifact_type: plan
tags: [ai, documentation, process-improvement]
---

# Plan: TCK-20261108-DOCS-REQUIRING-UPDATE-BUILT-BY-SEARCH

Design source: origin/lead-docs-review-source:agent-working/lead/docs_as_review_source_plan.md (rev 3.2, content @ d1fa1263c), "Owner correction (2026-11-07)" F1/F5, "Normative sources and precedence (R3)", acceptance criterion 1. Cited, not copied.

## What gets built
One reusable function, `tools/gate_checks/docs_search.py::search_docs_for_change`, with a MARKER-JSON CLI like the other gate_checks. Everything else (investigator prompt, doc-updater, staleness advisory) calls it.

**Inputs:** changed paths (planned paths at Investigate, the real diff at the gate), optional old-behaviour terms, an optional `--ref` that pins the docs tree being searched (a SHA, so a replay is repeatable), the repo root.
**Derived inputs:** (a) public symbols: `def`/`class` names found in the changed files' own source; (b) old-behaviour terms: stems of deleted and renamed paths, plus any `--old-term`; (c) importers: files that import a changed module, from `graphify-out/graph.json` (`imports`/`imports_from` edges) when it loads, else a regex scan of `src/`; the output says which one ran; (d) mechanisms: `registries/mechanisms.yaml` entries whose `implemented_by` cites a changed path, and the docs those entries cite.
**Search scope:** `docs/` and `README.md` (item 5 of the audit is in README.md:141). Text files only (`.md`, `.yaml`, `.yml`, `.html`, `.json`, `.csv`, `.txt`); a path hit is the changed path, its dotted module form, or its basename.

**Output** (a dict, also printed as MARKER JSON): `required`, `candidate`, `excluded` (each item `{path, hits:[{kind,line,text}], reason}`), `comment_hits` (F5), `notes` (graph or fallback, the docs ref, counts).

## Classification (one function, unit-tested per class)
1. **excluded**, checked first, each with its class as the reason:
   - `archive`: under `docs/archive/`; `audit`: under `docs/audits/`; `registry`: `docs/REGISTRY.yaml`.
   - `historical-plan`: frontmatter `status` is `historical` or `superseded`.
   - `review-record`: a dated review or report (see open question 1): file stem ends `_review`, `_report`, `_audit` or `_soak_review`.
2. **required**: a direct hit (path, symbol or old term) in a normative doc: `docs/world_rules/`, `docs/mechanics/`, `docs/engine/` (not `matrices/`), `docs/architecture/*_contract.md`. R3 order: normative first.
3. **candidate**: every other hit, ranked direct hit, then symbol or term, then importer, then mechanism. `docs/parity_ledger/` hits are candidates marked `owner: parity-updater` (doc-updater does not edit them).
Exact classification inputs only: no scoring, no thresholds, nothing tuned to the known items.

## F5 (comments and docstrings)
For each changed file that is Python, collect comment lines and docstring lines that contain an invariant, lifecycle, concurrency or recovery keyword (a fixed list in the module: invariant, must, never, always, lifecycle, concurren, recover, restore, ack, deterministic). Output `comment_hits` as `{path, line, text}`. Other comments are not returned. The list is a prompt aid for the investigator and doc-updater, not a verdict.

## Wiring
- `.claude/agents/investigator.md` ("Docs Requiring Update") and the Investigate prompt in `implement-ticket.js` (:948): run the CLI with the ticket's planned code paths; put `required` in Format 1 bullets (the only thing `check_docs_to_update_coverage` parses), `candidate` in a table, `excluded` in a table with reasons. Neither table uses a leading `- ` + backticked docs path, so the Verify parser, which reads only Format 1 bullets, is untouched (a test asserts this against the real regex).
- `docs_to_update` in the investigator schema stays the required list. Candidates do not make Verify block.

## Replay (acceptance criterion 1)
Two fixtures, pinned: #837 (`531010a9a`, base `531010a9a^`) and #786 (`6d3f6235c`, base `33da13604`). Committed under `tests/tools/fixtures/docs_search/` as a minimal docs subset: the cited lines of items 1, 2, 5, 6 and 9 and a few decoys (one per exclusion class), plus the changed-path lists and old terms. A separate script, `tools/gate_checks/docs_search_replay.py`, runs the same function against the real git tree at those SHAs and prints per-path candidate counts; I record those in the ticket (measured, not tuned).

## Open questions for the planner and designer
1. **Item 9 is not a hit on the #837 or #786 diffs.** `import_linter_soak_review.md` cites neither `executor.py`, `worker_manager`, `worker_protocol` nor any #786 path (checked with `git grep` at the base SHAs), and its frontmatter says `status: active`, so the plan's frontmatter rule does not exclude it. Criterion 1 can hold only if (a) a name-pattern class `review-record` excludes it and (b) the fixture includes a diff that does hit it. Recommendation: do (a) as above, and add a third fixture, the #817 diff (the change that made the phase19 contract enforced), to carry item 9. The class's cost: a live doc named `*_report.md` is never searched. I'll list the files it excludes under `docs/` in the ticket so you can judge.
2. Planned paths versus the real diff: at Investigate time the changed paths are only the ticket's Related Code Areas, so the Investigate list can miss files the implementation adds. The gate-time run (sibling ticket) uses the real diff and is the backstop.
3. `required` is "normative tier + direct hit", not "states the changed fact": the function cannot read meaning. The investigator confirms each required entry, and the output says so.

## Out of scope (as ticketed)
doc-updater satellite step and the gate advisory (sibling ticket); topic map; editing any doc found by the replay.
