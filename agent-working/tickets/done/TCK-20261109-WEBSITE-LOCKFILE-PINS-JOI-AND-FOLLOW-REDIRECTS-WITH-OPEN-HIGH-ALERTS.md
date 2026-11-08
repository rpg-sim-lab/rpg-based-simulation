---
status: historical
layer: misc
authority: P1
audience: agent
ticket_id: TCK-20261109-WEBSITE-LOCKFILE-PINS-JOI-AND-FOLLOW-REDIRECTS-WITH-OPEN-HIGH-ALERTS
phase: done
date: 2026-11-09
tags: []
---

# TCK-20261109-WEBSITE-LOCKFILE-PINS-JOI-AND-FOLLOW-REDIRECTS-WITH-OPEN-HIGH-ALERTS

## Title
The docs website's lockfile pins joi 17.13.8 and follow-redirects 1.16.1, which have open high Dependabot alerts

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
Dependabot opened two high alerts on `website/package-lock.json` on 2026-11-08 at 17:18:
- #252: `joi` 17.13.8, quadratic-time split in `string().email({ multiple: true })` (denial of service). Fixed in 17.13.9.
- #251: `follow-redirects` 1.16.1, cross-realm sensitiveHeaders arrays are discarded, so custom credentials can follow redirects. Fixed in 1.16.2.

The lockfile versions were the same before #846, so these are newly published advisories, not a regression. The owner approved the fix on 2026-11-09: "Yes, hotfix + README (Recommended)" (#715 comment 6724653808).

## Scope
- Refresh `website/package-lock.json` so `joi` resolves to 17.13.9 or later and `follow-redirects` to 1.16.2 or later.
- Both parents' ranges already allow the patched versions: `@docusaurus/types` and `@docusaurus/utils-validation` ask `joi ^17.9.2`, and `http-proxy` asks `follow-redirects ^1.0.0`. So no `overrides` entry is needed.

## Out of Scope
- Alert #249, `deepmerge` 4.3.1, which has no patched version.
- Alert #250, `minimatch` in `frontend/`. That's rpg-owned; the owner chose option A for it (#715 comment 6724653808).
- Any other dependency bump in `website/`.
- Adding a `/website` entry to `.github/dependabot.yml` (platform-owned, #845).

## Acceptance Criteria
- `website/package-lock.json` has `joi` >= 17.13.9 and `follow-redirects` >= 1.16.2, and no older copy of either remains.
- The lockfile diff changes only those two packages' entries.
- `npm run build` in `website/` succeeds.

## Related Tickets
- TCK-20261108-WEBSITE-DEV-SERVER-PULLS-A-UUID-WITH-AN-OPEN-SECURITY-ALERT (the previous website alert fix)
- TCK-20261109-README-NAMES-A-CHECKPOINT-SEED-DEFECT-THAT-IS-FIXED (same PR)

## Related Docs
None.

## Related Stored Artifacts
None (hotfix).

## Related Code Areas
website/package-lock.json

## Assumptions / Open Questions
- joi 17.13.9 and follow-redirects 1.16.2 are patch releases with no API change. The website build checks that.

## Implementation Notes
Ran `npm update joi follow-redirects --package-lock-only` in `website/` (Node 20.19.4, npm 9.2.0). Both parents' ranges already allowed the patched versions, so no `overrides` entry was added. The lockfile diff touches only the `node_modules/joi` entry (17.13.8 to 17.13.9) and the `node_modules/follow-redirects` entry (1.16.1 to 1.16.3, the newest patch, which includes the 1.16.2 fix). npm 9 also dropped the two entries' `license` fields.

## Test Summary
- Under `systemd-run --user --scope -p MemoryMax=3G -p MemorySwapMax=0 taskset -c 4-5`: `npm ci` from the new lockfile, then `node -e` printed joi 17.13.9 and follow-redirects 1.16.3, and `joi.string().email({multiple: true})` validated `a@b.com,c@d.org` with no error.
- `npm run build` exited 0 with "[SUCCESS] Generated static files in \"build\"".
- The lockfile has one entry each for joi and follow-redirects.
- Not run: `npm run start` (the dev server).

## Files Changed
- website/package-lock.json

## Completion Summary
Done. joi is 17.13.9 and follow-redirects is 1.16.3 in `website/package-lock.json`, so Dependabot alerts #252 and #251 should close once this merges. Not done here: deepmerge #249 (no fix exists) and frontend minimatch #250 (rpg, TCK-20261109-FRONTEND-LINT-TOOLING-PULLS-A-MINIMATCH-OPEN-TO-GLOB-DOS).
