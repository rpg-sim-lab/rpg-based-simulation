---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20261108-WEBSITE-DEV-SERVER-PULLS-A-UUID-WITH-AN-OPEN-SECURITY-ALERT
phase: done
date: 2026-11-08
tags: []
---

# TCK-20261108-WEBSITE-DEV-SERVER-PULLS-A-UUID-WITH-AN-OPEN-SECURITY-ALERT

## Title
The docs website's dev server pulls uuid 8.3.2, which has an open medium Dependabot alert that no update PR will fix

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
This is option 2 of issue #845. The owner said "yes, fold option 2 into your PR" on 2026-11-08.

Dependabot alert #143 (medium) flags `uuid` 8.3.2 in `website/package-lock.json`. It is fixed in 11.1.1.
- It is pulled in transitively by `sockjs` (`^8.3.2`), on the Docusaurus dev-server path.
- `.github/dependabot.yml` has no npm entry for `/website`, so no Dependabot PR will ever raise this update. That's option 1 in #845, platform's.

## Scope
- Add a scoped `overrides` entry, `"sockjs": {"uuid": "^11.1.1"}`, to `website/package.json`, following the file's existing pattern for serialize-javascript and postcss-selector-parser.
- Regenerate `website/package-lock.json`.

## Out of Scope
- Alert #249, `deepmerge` 4.3.1. It has no patched version; dismiss it or wait (option 3 in #845).
- Adding a `/website` Dependabot entry. That's `.github/dependabot.yml`, platform-owned (option 1 in #845).
- Other dependency bumps in `website/`.

## Acceptance Criteria
- The lockfile resolves `sockjs`'s `uuid` to 11.1.1 or later, and no 8.x `uuid` remains.
- `require('uuid').v4` resolves from `sockjs`'s directory and returns a v4 UUID. `sockjs/lib/transport.js:9` uses exactly that call.
- `npm run build` in `website/` succeeds.

## Related Tickets
- TCK-20261108-DOC-TOPIC-MAP-NAMES-ONE-CANONICAL-SOURCE-PER-FACT-GROUP (same PR)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
website/package.json, website/package-lock.json

## Assumptions / Open Questions
- uuid 11 still exports a CommonJS `v4`. This is checked by the require check in the acceptance criteria.

## Implementation Notes
Added `"sockjs": {"uuid": "^11.1.1"}` to `website/package.json` `overrides`, then ran `npm install` (Node 20.19.4, npm 9.2.0). The lockfile diff touches only the `node_modules/uuid` entry: 8.3.2 becomes 11.1.1, and its bin path changes.

## Test Summary
- `node_modules/uuid` resolves to 11.1.1, the only `uuid` entry in the lockfile.
- `require('uuid').v4`, resolved from sockjs's directory, returned a valid v4 UUID. `require('sockjs/lib/transport.js')` loads.
- `npm run build` in `website/` exited 0 with "[SUCCESS] Generated static files", run capped at 3G on cores 4-5.
- Not run: `npm run start` (the dev server itself).

## Files Changed
- website/package.json
- website/package-lock.json

## Completion Summary
Done. sockjs's uuid is overridden to 11.1.1, so Dependabot alert #143 should close once this merges to main. Not done here: deepmerge alert #249 (no fix exists) and the `/website` Dependabot entry (platform, #845).
