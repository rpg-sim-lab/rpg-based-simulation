---
status: active
layer: platform
authority: P1
audience: agent
ticket_id: TCK-20261112-REPO-MOVE-PLATFORM-REFS
phase: open
date: 2026-11-12
tags: [platform, delivery]
---

# TCK-20261112-REPO-MOVE-PLATFORM-REFS

## Title
Platform files name the new repository owner rpg-sim-lab after the transfer

## Status
OPEN

## Tier
hotfix

## Type
repair

## Priority
P1

## Request Summary
The repository moved from ttnhan18062000/rpg-based-simulation to rpg-sim-lab/rpg-based-simulation (#715 6814855329,
6814867407). GitHub redirects the old URLs. Two platform files still name the old owner as a live value:
- `.github/workflows/deploy-docs.yml:51`: `DOCS_URL: https://ttnhan18062000.github.io`. The owner re-enabled Pages
  (source GitHub Actions). The site is now https://rpg-sim-lab.github.io/rpg-based-simulation/, and nothing has deployed
  there yet. A deploy with the old DOCS_URL would build canonical and sitemap URLs on the old host. No docs deploy is
  dispatched before this merges (lead-planner, 2026-11-12).
- `infra/terraform/bootstrap/variables.tf:9`: the `github_repository` default. It sets the OIDC trust subject
  `repo:<owner/name>:ref:refs/heads/<branch>` (`main.tf:31`), so an apply with the old default would trust a repository
  that no longer exists under that name.

## Scope
1. `deploy-docs.yml`: `DOCS_URL: https://rpg-sim-lab.github.io`. `DOCS_BASE_URL` stays `/rpg-based-simulation/`.
2. `variables.tf`: default `"rpg-sim-lab/rpg-based-simulation"`.
3. Check for any other old-owner value in platform-owned paths (`compose.yaml`, `docker/**`, `.github/**` except
   `test.yml`, `infra/**`, `tools/loadtest/**`, `docs/runbooks/**`, `docs/observability/loki_label_policy.md`). On
   2026-11-12 `git grep ttnhan18062000 origin/main` found only the two above in those paths.

## Out of Scope
- `tools/agent-monitoring/record_review.py:41`, `tools/delivery/ticket_queue.py:33` REPO constants (claimed on u24,
  #634 6814987021).
- `website/**`, including `website/scripts/generate_wiki.py:38` SOURCE_URL (lead-planner's).
- Historical links under `docs/` (they redirect; left as history, lead-planner-u24 6814867407).
- The local git remote URL (works via redirect; the owner's).
- Running a docs deploy, a Terraform plan or apply.

## Acceptance Criteria
- `git grep ttnhan18062000` over the platform-owned paths returns nothing (validated).
- `deploy-docs.yml` still parses and keeps `DOCS_BASE_URL: /rpg-based-simulation/`; `tests/static/test_deploy_docs_heap_limit.py`
  and `tests/static/test_ci_step_summary_reporting.py` pass (validated).
- `terraform fmt -check` and `terraform validate` pass for `infra/terraform/bootstrap` if terraform is on the host;
  otherwise the IaC workflow on the PR proves it (validated).
- After merge: the first Deploy Docs run on main serves https://rpg-sim-lab.github.io/rpg-based-simulation/ (observed
  after merge; until then: Known gap: the first deploy under the new owner is not yet observed).

## Related Tickets
- TCK-20261018-TERRAFORM-AWS-SKELETON, TCK-20261018-IAC-WORKFLOW-AND-ROLES (done; the bootstrap module).
- TCK-20260821-HOTFIX-GHPAGES-BUILD-OOM (done; deploy-docs heap limit).
- TCK-20261112-DEPENDABOT-IGNORE-KNOWLEDGE-STACK (same PR).

## Related Docs
None.

## Related Stored Artifacts
None.

## Related Code Areas
.github/workflows/deploy-docs.yml
infra/terraform/bootstrap/variables.tf

## Assumptions / Open Questions
- Checked by platform-planner on 2026-11-12 (read-only, `gh api` against the new repo): 0 repository secrets and 0
  variables, and the workflows use only `secrets.GITHUB_TOKEN`; environment `github-pages` exists with branch policy
  `main`; Pages `build_type: workflow`, html_url https://rpg-sim-lab.github.io/rpg-based-simulation/.
- GHCR: `publish-images.yml` uses `ghcr.io/${{ github.repository }}`, so images now go to `ghcr.io/rpg-sim-lab/...`.
  Unverified: whether the new organization's package settings allow a workflow to create packages. The first
  publish-images run shows it; if it fails, that is the owner's org setting.

## Implementation Notes
## Test Summary
## Files Changed
## Completion Summary
