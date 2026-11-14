---
status: historical
layer: website
authority: P2
audience: agent
ticket_id: TCK-20261114-WEBSITE-LINKS-NAME-THE-NEW-REPO-OWNER
phase: done
date: 2026-11-14
tags: [documentation]
---

# TCK-20261114-WEBSITE-LINKS-NAME-THE-NEW-REPO-OWNER

## Title
The wiki's source links name the repository's new owner, rpg-sim-lab

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
The repository moved from `ttnhan18062000/rpg-based-simulation` to `rpg-sim-lab/rpg-based-simulation` on 2026-11-12 (#715 6814855329). Platform fixed its own references in #894 and agent-working's two REPO constants were claimed on u24 (#634 6814987021). Three lead-owned `website/**` references still named the old owner. GitHub redirects them, so nothing was broken, but every generated "source" and "edit" link on the live wiki pointed at the old URL.

## Scope
- `website/scripts/generate_wiki.py:38` `SOURCE_URL` (feeds `custom_edit_url` and the per-page source links of every generated world-knowledge page).
- `website/wiki/technical/index.md:11` and `website/wiki/world-knowledge/index.md:21` (hand-written links into `docs/`).

## Out of Scope
- Historical docs, tickets and records that cite old PR/issue URLs (they redirect and are records).
- Other domains' files.

## Acceptance Criteria
1. `git grep ttnhan18062000 -- website/` returns nothing (excluding node_modules).
2. The wiki static tests still pass.

## Related Tickets
- TCK-20261112-REPO-MOVE-PLATFORM-REFS (#894)

## Related Docs
- `docs/README.md` ("Documentation Site")

## Related Stored Artifacts
None.

## Related Code Areas
- `website/scripts/generate_wiki.py`

## Assumptions / Open Questions
None.

## Implementation Notes
A one-string substitution of the owner part of the URL in three places, by lead-planner (website/** owner).

## Test Summary
`pytest tests/static/test_website_wiki_generator.py tests/static/test_website_wiki_site_shape.py`: 18 passed. `git grep ttnhan18062000 -- website/`: 0 hits.

## Files Changed
- `website/scripts/generate_wiki.py`
- `website/wiki/technical/index.md`
- `website/wiki/world-knowledge/index.md`

## Completion Summary
The three links now use `https://github.com/rpg-sim-lab/rpg-based-simulation/`. The live site picks them up on the next deploy, which this merge triggers (website/** is on the deploy-docs paths filter).
