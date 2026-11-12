---
status: historical
layer: website
authority: P2
audience: agent
ticket_id: TCK-20261111-WEBSITE-WIKI-VIEWS-OF-STORED-DATA
artifact_type: test_plan
tags: [documentation, onboarding]
---

# Test plan

## tests/static/test_website_wiki_generator.py
- Real data: every world-rule heading and statement is on its family page (count and text); every mechanism appears once on its layer page; the state and cadence labels cover the registry's vocabulary; each catalog page has one row per stored entry; every page's `source_docs` exist.
- Fixtures: summary shown only when present (and nothing else changes); glossary skipped when absent or empty and rendered when filled; generate clears only the generated folders; multi-line and missing statements parse; table cells escape `|`, `<`, `>`, `{`, `}`.

## tests/static/test_website_wiki_site_shape.py
- docs/ not rendered; search over the wiki only; three sidebars, tabs and landing pages; broken links throw; the generator runs before build and start; generated folders gitignored; removed sidebar files stay deleted; the homepage links the three spaces.

## Also run
- `npm run build` in website/ (AC1), under the 3 GB wrapper.
- `tests/static/test_deploy_docs_heap_limit.py`, `tests/tools/test_parity_index_baseline.py`, the parity schema ratchet.
