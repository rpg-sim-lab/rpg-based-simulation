---
status: historical
layer: guidelines
authority: P1
audience: agent
ticket_id: TCK-20261111-CLAUDE-MD-REGISTRY-DRIVER-WORDING
phase: done
date: 2026-11-11
tags: [claude-md]
---

# TCK-20261111-CLAUDE-MD-REGISTRY-DRIVER-WORDING

## Title
CLAUDE.md says the registry merge driver regenerates after rebase and cherry-pick; it does so only after a plain `git merge`

## Status
DONE

## Tier
hotfix

## Type
repair

## Priority
P2

## Request Summary
CLAUDE.md "After Work" said the `docs/REGISTRY.yaml` merge driver "only helps local `git merge`/rebase/cherry-pick operations". That is wrong. `tools/hooks/registry_post_merge_regen.sh:21-24` says rebase and cherry-pick invoke the driver but never run the regeneration hook. A merge that stops on another conflict and is finished with `git commit` never runs post-merge either, which is how 4919e81f8 got a stale registry. Finding from agent-working-designer-u24, relayed by lead-planner-u24. Owner approved the fix (#715 6785323244), in the form without the post-commit clause, which waits for the post-commit hook hotfix (`TCK-20261111-REGISTRY-REGEN-MISSES-A-MERGE-FINISHED-BY-COMMIT`, PR #865).

## Scope
- The one sentence in CLAUDE.md "After Work" on what the registry merge driver covers.

## Out of Scope
- The post-commit clause (`make install-hooks`); it is added after #865 lands.
- Any change to the hook, the driver or the CI test.

## Acceptance Criteria
- CLAUDE.md says the driver regenerates only after a plain local `git merge` (post-merge).
- It names rebase, cherry-pick and a merge finished with `git commit` as paths that keep one side.
- It names the CI test that catches that (`tests/tools/test_generate_registry.py::TestRealDocsTree::test_check_flag_detects_no_drift_against_real_registry`) and says to run `make docs-registry` after any of them.
- The server-side merge-ref sentence is kept.

## Related Tickets
- TCK-20260912-REGISTRY-YAML-MERGE-CONFLICT-TAX (the driver)
- TCK-20261111-REGISTRY-REGEN-MISSES-A-MERGE-FINISHED-BY-COMMIT (u24 post-commit hotfix, #865)

## Related Docs
- CLAUDE.md ("After Work")
- tools/hooks/registry_post_merge_regen.sh (header, lines 18-26)

## Related Stored Artifacts
- none (hotfix)

## Related Code Areas
- tools/hooks/registry_post_merge_regen.sh (read only)

## Assumptions / Open Questions
- When #865 lands, a follow-up adds "or a merge finished with `git commit` (post-commit, via `make install-hooks`)" to the regenerating paths.

## Implementation Notes
One sentence replaced in place in CLAUDE.md. No test pins the old wording (searched tests/, tools/, .claude/).

## Test Summary
- `tests/docs/test_prescan_mandate_instruction_draft.py`, `tests/tools/test_governing_edit_visibility.py`, `tests/integrity/test_registry_merge_driver.py`: 39 passed, 1 skipped (2026-11-11, before the closing commit).
- `tools/generate_registry.py --check` in sync after `make docs-registry`.

## Files Changed
- CLAUDE.md
- agent-working/tickets/done/TCK-20261111-CLAUDE-MD-REGISTRY-DRIVER-WORDING.md
- agent-working/tickets/working_log.csv (via the closure tool)
- docs/REGISTRY.yaml
- agent-working/agent-monitoring/ (monitoring rows)

## Completion Summary
The CLAUDE.md sentence now matches what the hook does: the driver regenerates only after a plain local `git merge`; rebase, cherry-pick and a merge finished with `git commit` keep one side, which only the CI no-drift test catches, so run `make docs-registry` after them. Owner approval #715 6785323244.
