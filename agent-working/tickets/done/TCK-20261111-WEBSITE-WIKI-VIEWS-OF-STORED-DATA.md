---
status: historical
layer: website
authority: P1
audience: agent
ticket_id: TCK-20261111-WEBSITE-WIKI-VIEWS-OF-STORED-DATA
phase: done
date: 2026-11-11
tags: [documentation, onboarding]
---

# TCK-20261111-WEBSITE-WIKI-VIEWS-OF-STORED-DATA

## Title
The website becomes a wiki for someone watching the simulation, built from the repository's stored data instead of rendering docs/

## Status
DONE

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Issue #845. The owner wants the website restructured as a wiki without implementation detail or tickets (#715 6787349389). The reader is someone watching a simulation run who wants its terms and concepts. The site has three spaces: World Knowledge (filled now), plus Technical and Control Guide (placeholders, filled later) (#715 6789714730). Owner rule (#715 6789779149): the wiki is a UI view of the stored mechanism data, registries and content files, with no logic split between the wiki and the repository's documents. So every World Knowledge fact page is generated at build time from a source file and never committed. Docusaurus stays.

## Scope
- `website/scripts/generate_wiki.py`: renders Laws of the World (`docs/world_rules/`: rule ID, title, quoted statement), How the World Runs (`registries/mechanisms.yaml`, `system_registry.jsonl`, `mechanism_causal_edges.yaml`), Who and What Is in the World (`data/content/`, all entries as stored) and a Glossary (`registries/world_glossary.jsonl`, skipped while absent or empty).
- Docusaurus config: docs path `wiki`, three sidebars and navbar tabs, search over the wiki only, broken links fail the build; `docs/` is no longer rendered.
- Hand-written landing pages for the three spaces (layout and pointers only, no rules or facts) and a new homepage.
- Generated folders gitignored; npm `prebuild`/`prestart` run the generator; Makefile `docs-serve`/`docs-build` no longer depend on `docs-artifacts`.
- Tests for the site shape and for the generator against its sources; parity entry INFRA-181 updated; README.md and docs/README.md describe the wiki.
- New layer `website` registered.

## Out of Scope
- Writing mechanism summaries: rpg-planner's `TCK-20261111-EACH-MECHANISM-GETS-A-PLAIN-LANGUAGE-SUMMARY` (u24). The wiki shows them once merged.
- The world glossary registry and its terms: agent-working's `TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY` (tool) and a later rpg ticket (terms).
- Technical and Control Guide content.
- Publishing: `TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING` (the deploy runner will also need PyYAML for the generator; noted there).
- Dependabot for `website/` (platform-planner; #845 option 1).

## Acceptance Criteria
1. `npm run build` in `website/` generates the pages and builds with zero broken links and no duplicate routes.
2. Every rule heading in `docs/world_rules/<area>/*.md` (not review-exports or scenarios) appears on its family page with its stored statement; every mechanism appears once on its layer page; each catalog page has one row per stored entry.
3. Every generated page names its source files in `source_docs` frontmatter and a footer link, and every named source exists.
4. A mechanism `summary` shows only when the registry has one; the Glossary page appears only when `registries/world_glossary.jsonl` has rows.
5. Generated folders are gitignored; the generator clears only those folders.
6. `docs/` is not rendered and search covers the wiki only; the homepage links the three spaces.
7. The generator holds presentation only (layout, column choice, plain labels for stored enum values); no rule, mechanism or content value is written in it.

## Related Tickets
- TCK-20260821-DOCS-BUILD-LASTUPDATE-METADATA-OVERHEAD (the docs/ subset this replaces)
- TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING (publishing, not in scope)
- TCK-20261111-EACH-MECHANISM-GETS-A-PLAIN-LANGUAGE-SUMMARY (rpg, u24)
- TCK-20261111-WORLD-TERM-GLOSSARY-REGISTRY, TCK-20261111-MECHANISM-SUMMARY-FIELD-SHAPE-CHECK (agent-working)

## Related Docs
- docs/world_rules/README.md
- registries/mechanisms.yaml (header: state vocabulary, layers)
- docs/mechanics/content_usage_matrix.md
- docs/README.md ("Documentation Site"), README.md ("Documentation Site")

## Related Stored Artifacts
- agent-working/stored_artifacts/TCK-20261111-WEBSITE-WIKI-VIEWS-OF-STORED-DATA/ (plan, investigation, test_plan)

## Related Code Areas
- website/
- tests/static/

## Assumptions / Open Questions
- Rule statements are rendered as stored. Some quote other rule IDs or code names; changing that wording belongs in the World Rule Catalog, not the wiki.
- No file records which catalog entries a default world uses, so the catalog shows every stored entry (a filter would be wiki-side logic).

## Implementation Notes
See plan.md.

## Test Summary
- `tests/static/test_website_wiki_generator.py` (10) and `tests/static/test_website_wiki_site_shape.py` (8): pass. With the rest of `tests/static`, `tests/tools/test_layer_registry.py`, `test_ticket_field_values.py`, `test_validate_frontmatter.py`: 318 passed (2026-11-11).
- Tests near the layer and registry changes (`test_add_frontmatter_tickets`, `test_agent_ops_dashboard_*`, `test_delivery_pr_render`, `test_glossary_registry`, `test_tag_category_registry`, `test_ticket_stats_report`, `tests/unit/tools/test_system_registry`, `test_generate_registry`): 316 passed.
- `tests/tools/test_parity_index_baseline.py`: 15 passed; parity schema ratchet: 0 rose, 0 new.
- `npm ci` then `npm run build` in `website/` under the 3 GB wrapper: 46 law, 6 mechanism and 16 catalog pages generated, 87 HTML pages built, no broken links, no duplicate routes.
- ruff on `website/scripts/generate_wiki.py`: clean.

## Files Changed
- website/scripts/generate_wiki.py (new), website/.gitignore (new), website/wiki/{world-knowledge,technical,control-guide}/index.md (new)
- website/docusaurus.config.js, website/sidebars.js, website/package.json, website/src/pages/index.js; website/sidebars-archive.js (deleted)
- tests/static/test_website_wiki_generator.py, tests/static/test_website_wiki_site_shape.py (new); tests/static/test_docs_build_content_scope.py (deleted)
- tests/tools/test_layer_registry.py, tests/tools/test_validate_frontmatter.py (pinned layer set gains `website`)
- registries/layer_registry.jsonl (layer `website`)
- docs/parity_ledger/infrastructure.yaml (INFRA-181), docs/README.md, README.md, Makefile
- agent-working/tickets/done/TCK-20261111-WEBSITE-WIKI-VIEWS-OF-STORED-DATA.md, agent-working/stored_artifacts/TCK-20261111-WEBSITE-WIKI-VIEWS-OF-STORED-DATA/, agent-working/tickets/working_log.csv, docs/REGISTRY.yaml, agent-working/agent-monitoring/

## Completion Summary
The website is now a wiki with three spaces. World Knowledge is generated at build time from the World Rule Catalog (189 rules in 46 families), the mechanism registry (110 mechanisms on 5 layer pages plus an overview) and the content catalog (16 tables), and shows mechanism summaries and a glossary as soon as their sources have them. Nothing generated is committed. Technical and Control Guide have landing pages for later. `docs/` is no longer rendered. `make knowledge-index-update` was not run: the embedding model runs out of memory on this host (known; agent-working-planner's OOM ticket). Publishing stays with TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING, whose deploy runner will need PyYAML for the generator.
