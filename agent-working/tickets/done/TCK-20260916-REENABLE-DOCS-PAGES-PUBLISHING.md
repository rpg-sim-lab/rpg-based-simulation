---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING
phase: done
date: 2026-09-16
tags: [documentation, process-improvement]
---

# TCK-20260916-REENABLE-DOCS-PAGES-PUBLISHING

## Title
Re-enable GitHub Pages docs publishing once the docs site is ready to publish a first version

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P3

## Request Summary
Placeholder-by-design, filed at the user's request 2026-09-16 alongside
`TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW`, so that temporarily disabling the docs deploy
workflow does not quietly become permanently forgetting it.

**Why it is blocked:** the user's reasoning, verbatim in substance — *the main logic is still being
developed and is not yet ready to publish the first version*. Enabling GitHub Pages today would
publish a docs site that does not yet represent the project. This is a deliberate scheduling
decision, not an oversight or a defect.

**Current state:** `gh api repos/:owner/:repo/pages` returns **404** (Pages not enabled), and
`.github/workflows/deploy-docs.yml` has been narrowed so it no longer fires on push to `main` —
see the disable ticket for the full diagnosis, including that the failure was invisible for days
because no PR ever exercises that lane.

## Scope
When the docs are ready to publish:

- Enable GitHub Pages for the repository (a settings change, and the user's call — not an agent's).
- Restore `deploy-docs.yml`'s `push: branches: [main]` trigger, reverting the disable.
- Verify an actual published page renders, not merely that the workflow went green — a successful
  deploy step is not evidence the site is correct or reachable.
- Check whether anything in the repo already assumes a published site exists (README badges,
  cross-links) and reconcile it.

## Out of Scope
- Any work on the docs content itself. This ticket is only the publishing mechanism.
- Re-enabling early "because CI is red". The lane is disabled, not failing, so there is no CI
  pressure to act on — that was the point of disabling rather than deleting.

## Acceptance Criteria
- [x] GitHub Pages is enabled and `gh api repos/:owner/:repo/pages` returns a real site, not 404. (observed 2026-11-12: `build_type=workflow`, `html_url=https://rpg-sim-lab.github.io/rpg-based-simulation/`, `https_enforced=true`; the owner enabled it after the repository moved.)
- [x] `deploy-docs.yml` fires on push to `main` again, and its in-file disable comment is removed. (validated: the file parses with `push: branches: [main]`, a `paths` filter and `workflow_dispatch`; the header comment is gone. The first push-triggered run is not yet observed: Known gap.)
- [x] A published page is fetched and inspected — verified as rendering real content, not just a
      green check-run. (observed 2026-11-12: the front page, and three inner pages, see Test Summary.)
- [x] `TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW` is cross-referenced as resolved-by-this. (done: a "Resolved by" line on that ticket's Completion Summary, and this ticket's Related Tickets.)

## Related Tickets
- `TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW` — the temporary disable this reverses; **resolved by this ticket** (2026-11-12)
- `TCK-20261112-REPO-MOVE-PLATFORM-REFS` — set `DOCS_URL` to the new owner's host (merged, #894)

## Related Docs
- None yet.

## Related Stored Artifacts
- None yet.

## Related Code Areas
- `.github/workflows/deploy-docs.yml`

## Assumptions / Open Questions
- **Unblock condition is a judgement call, not a measurable one**: "the docs are ready to publish a
  first version" is the user's decision. Do not self-authorise it from CI state or from the docs
  merely building successfully.
- Whether Pages should serve from a branch or from the Actions artifact: settled by the owner, `build_type=workflow` (the Actions path), and by the first manual deploy.
- The first real run must also confirm actions/upload-pages-artifact@v5 (#588) and setup-node@v7 with Node 24 (TCK-20261018-RUNNER-UBUNTU-26-AND-NODE24); neither has executed. deploy-docs.yml is platform-owned since 2026-10-18.

## Implementation Notes
Was blocked until the owner said the docs were ready to publish; that happened on 2026-11-12 (below).

Observed 2026-11-12 (platform-planner; this records progress, the ticket is not closed):
- After the repository moved to rpg-sim-lab (#715 6814855329), the owner re-enabled Pages with source GitHub Actions. `gh api repos/rpg-sim-lab/rpg-based-simulation/pages` gives `build_type: workflow` and html_url https://rpg-sim-lab.github.io/rpg-based-simulation/. AC 1 is met.
- The owner ran the first deploy by hand: Deploy Docs run 43203095497 (workflow_dispatch, at 0539145cb), success. It is the first execution of actions/upload-pages-artifact@v5 and actions/setup-node@v7 with Node 24 here, which answers the open question above.
- The published page was fetched: 200, title "RPG Simulation Wiki", canonical and og:url on the new host. That partly covers AC 3: the front page renders. No inner pages were inspected.
- Still open: AC 2 (restore `push: branches: [main]` and remove the in-file disable comment) and AC 4 (the cross-reference). Restoring the trigger is the owner's call, per Assumptions above.

Implemented 2026-11-12 (platform-implementer; dispatched by platform-planner):
- **Owner decision A on #715 6821987369** ("A: auto-deploy on main"): restore the push trigger, drop the disable comment, **re-tier this ticket from standard to hotfix** (a trigger change in one file), check two or three inner pages, close in the next PR. That decision is also the "docs are ready to publish" call the Assumptions asked for.
- `.github/workflows/deploy-docs.yml`: the "Temporarily disabled" header is removed; `on:` is `push: branches: [main]` with a `paths` filter, plus the existing `workflow_dispatch`; a short comment says why the filter exists (a merge that changes nothing the site is built from must not redeploy it) and points at this ticket.
- **The filter, checked against the build.** The build is `cd website && npm run build`, which runs `prebuild` = `python3 scripts/generate_wiki.py`, then `docusaurus build`. Docusaurus reads only `website/` (its own docstring says `docs/` is not rendered; the generated pages go to `website/wiki/world-knowledge`). `generate_wiki.py` reads from outside `website/` exactly these: `docs/world_rules/**` (`WORLD_RULES_DIR`), `registries/mechanisms.yaml` (`MECHANISMS`), `registries/system_registry.jsonl` (`SYSTEMS`), `registries/mechanism_causal_edges.yaml` (`CAUSAL_EDGES`), `registries/world_glossary.jsonl` (`WORLD_GLOSSARY`) and **`data/content/**` (`CONTENT_DIR`, the content catalog; 67 tracked files)**. The filter planned in the dispatch listed everything but `data/content/**`; without it a merge that changes only the content catalog would not redeploy the catalog pages. So the filter is `website/**`, `!website/node_modules/**`, `docs/world_rules/**`, `data/content/**`, the four registry files, and `.github/workflows/deploy-docs.yml`. The old pre-#211 filter (`docs/**`, `tickets/done/**`, `stored_artifacts/**`, `website/**`) is stale after the move into `agent-working/` and is not restored.
- This ticket's own PR changes `deploy-docs.yml`, which is on the filter, so its merge should trigger the first push-based deploy.
- Reconcile (scope item 4): outside `website/`, nothing in the repo assumes a published site (no README badge, no old-host Pages link in `README.md`, `docs/`, `tools/`, `.github/`, `compose.yaml`, `docker/` or `infra/`). Three files under `website/` still name the old owner (`website/scripts/generate_wiki.py`, `website/wiki/technical/index.md`, `website/wiki/world-knowledge/index.md`); `website/**` is lead's and is not touched here.

## Test Summary
- **validated:** `tests/static/test_deploy_docs_heap_limit.py`, `tests/static/test_ci_step_summary_reporting.py` and `tests/static/test_website_wiki_site_shape.py`: 24 passed. No test pins the trigger (`git grep` over `tests/` finds `deploy-docs.yml` only in those tests, in `tests/tools/test_delivery_pr_status.py` as a path string, and in a fixture). The workflow parses: `on` has `push` (branches `[main]`, 9 path entries) and `workflow_dispatch`; the Build step still has `DOCS_URL`, `DOCS_BASE_URL` and `NODE_OPTIONS` unchanged.
- **observed (inner pages, 2026-11-12, `https://rpg-sim-lab.github.io/rpg-based-simulation/`; the sitemap lists 87 pages):**
  - `.../wiki/world-knowledge/laws/capability-progression/conflict-combat`: 200, title "Conflict / Combat | RPG Simulation Wiki", canonical on the new host; real content: its rule ids (AGENCY-02, AGENCY-07, CONFLICT-01, CONFLICT-03, CONFLICT-04) are all in `docs/world_rules/capability-progression/conflict-combat.md`.
  - `.../wiki/world-knowledge/mechanisms/entity`: 200, title "Entity layer | RPG Simulation Wiki", canonical on the new host; 12,344 characters of visible text on layers, state and mechanisms.
  - `.../wiki/world-knowledge/catalog/biomes`: 200, title "Biomes | RPG Simulation Wiki", canonical on the new host; the biome names frontier_village, near_forest and wolf_den from `data/content` are on the page.
  - Earlier the same day the front page: 200, title "RPG Simulation Wiki" (platform-planner).
- **observed:** the first manual deploy, run 43203095497 (`workflow_dispatch`, at 0539145cb), succeeded; it was the first execution of upload-pages-artifact v5 and setup-node v7 with Node 24 here. Before it, the last runs of this workflow were the failing pushes of 2026-09-16.
- **not observed:** the first push-triggered deploy (it comes with this PR's merge).


## Files Changed
- `.github/workflows/deploy-docs.yml`: disable header removed; `push: branches: [main]` with a `paths` filter restored; comment on why the filter exists.
- `agent-working/tickets/done/TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW.md`: one "Resolved by" line (AC 4).
- this ticket (re-tiered to hotfix, moved to done/).


## Completion Summary
GitHub Pages now publishes the docs site from `main` automatically. The owner enabled Pages (workflow source) after the repository moved and ran the first deploy by hand (run 43203095497, success); on owner decision A (#715 6821987369) `.github/workflows/deploy-docs.yml` fires on `push` to `main` again, filtered to the paths the build reads (`website/**`, `docs/world_rules/**`, `data/content/**`, four `registries/` files and the workflow itself), with `workflow_dispatch` kept and the disable comment removed. The filter was checked against `website/scripts/generate_wiki.py` and the Docusaurus config: it adds `data/content/**`, which the dispatch's draft list had missed. Three inner pages of the live site (a law family, a mechanism layer, a catalog family) were fetched: 200, correct titles and canonicals, and content that matches this repository's sources. `TCK-20260916-DISABLE-DOCS-PAGES-DEPLOY-WORKFLOW` carries a "Resolved by" line. Re-tiered from standard to hotfix by the owner's decision.
Known gap: the first push-triggered deploy is not yet observed; it should come with this PR's merge, because the PR changes `deploy-docs.yml`, which is on the filter. A merge that changes none of the filtered paths will, by design, not redeploy.
Also not covered: three files under `website/` still name the old owner (lead's; `website/**` was not touched), and the filter will need a new entry if `generate_wiki.py` starts to read another path outside `website/`.
