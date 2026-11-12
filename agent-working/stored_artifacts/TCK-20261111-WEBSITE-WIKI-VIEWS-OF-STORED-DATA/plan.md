---
status: historical
layer: website
authority: P2
audience: agent
ticket_id: TCK-20261111-WEBSITE-WIKI-VIEWS-OF-STORED-DATA
artifact_type: plan
tags: [documentation, onboarding]
---

# Plan

## Principle
The wiki is a view (owner, #715 6789779149). A fact appears on the site only because a source file holds it. The generator decides layout, columns and plain labels for stored enum values, nothing else. Generated pages are never committed, so they cannot drift.

## Steps
1. `website/scripts/generate_wiki.py` (Python, PyYAML from the project environment), writing into `website/wiki/world-knowledge/{laws,mechanisms,catalog,glossary}/`:
   - Laws: one page per rule family under its area; each rule as `## ID — Title` plus its quoted statement; explicit slugs so a family named like its area folder does not collide with the area index.
   - Mechanisms: an overview (layers with cadence and counts, systems, state counts) and one page per layer; each mechanism heading carries a stable anchor; `summary` when present; Needs (`depends_on`) and Feeds (causal edges) link across layer pages.
   - Catalog: one table per content family (16 pages), references shown by display name; factions add a relationships table.
   - Glossary: from `registries/world_glossary.jsonl` when it has rows.
   - Every page: `source_docs` frontmatter, a footer naming its sources, `custom_edit_url` when there is one source.
2. Config: docs path `wiki`, route `wiki`, three sidebars and navbar tabs, search over `wiki`, `onBrokenLinks: 'throw'`; delete `sidebars-archive.js`; new homepage; landing pages for the three spaces.
3. `website/.gitignore` for the generated folders; npm `generate`, `prebuild`, `prestart`; Makefile `docs-serve`/`docs-build` lose the stale `docs-artifacts` prerequisite.
4. Tests: replace `test_docs_build_content_scope.py` with `test_website_wiki_site_shape.py`; add `test_website_wiki_generator.py`.
5. Docs: README.md and docs/README.md; parity INFRA-181; register layer `website`.

## Acceptance map
AC1 build; AC2-AC5 generator tests; AC6 site-shape tests; AC7 review of the generator (no stored values in it).
