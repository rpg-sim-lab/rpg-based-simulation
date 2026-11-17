---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261115-SDLC-BASELINE-TAG-RULESET
phase: done
date: 2026-11-15
tags: [ai, governance, security]
---

# TCK-20261115-SDLC-BASELINE-TAG-RULESET

## Title
A tag ruleset protects the four frozen SDLC baseline tags, applied by the owner.

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
Split from TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION on 2026-11-15. The owner deferred the machine account, the credential removal, E6b and the M1 merge rule, and kept only this tag ruleset, which the owner applies (#715 6889309909, 6889318166). OD-15 (#715 6529263880) froze the baselines as tags. They are unprotected today (#715 6541773425), so any admin push can move or delete them.

## Scope
1. Read the repository's current rulesets fresh. The 10-31 export (`agent-working/stored_artifacts/sdlc-phase-0/ruleset_14220945_export.jsonl`) predates the 2026-11-12 move to the rpg-sim-lab organization and the owner's bypass restore (#715 6818960465), so it is not the before-state. Record the before-state.
2. Prepare, without running, the command or settings steps for one tag ruleset:
   - its rules are deletion, update and non-fast-forward, on a tag target pattern. The proposed pattern is `refs/tags/baseline/sdlc-*`; the exact pattern is named only after the fresh read in item 1, which shows what the org repo offers;
   - give the owner, or the admin role, bypass so the owner can still act;
   - change nothing on the branch ruleset.
3. The owner applies it, on its own ask through lead-planner, logged on #715.
4. Read the rulesets again and confirm the after-state. Show all four tags unchanged on both SHAs (AC3).

## Out of Scope
- The M1 merge rule and the branch ruleset (deferred, TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION).
- The machine account and credential removal (deferred).
- Creating, moving or deleting any tag.

## Acceptance Criteria
1. Before and after ruleset reads are recorded, with no credential detail.
2. A tag ruleset targeting the four `baseline/sdlc-*` tags exists, and the branch ruleset is unchanged.
3. After the change, `git ls-remote --tags origin 'baseline/*'` shows each of the four tags unchanged on both its tag-object SHA and its peeled commit. That way a tag moved to another tag object is caught. #715 6541773425 recorded the peeled commit, 6fdfdf5556548105e28ab370832f36bc96241561. The tag objects read on 2026-11-15 are:
   - `sdlc-agent-replay-20261031` 643b26a4ab3e780334cde1d9109640e9fbd3790b;
   - `sdlc-codex-track-20261031` 7924b36e1ff9f7651abfafb550126f3cff28e0e0;
   - `sdlc-pipeline-workflows-20261031` 060f25e4df95090e5e367ca5191aac4137fec027;
   - `sdlc-provider-neutral-contract-20261031` 91ef2ac8ec8d37c998c0e438d863767fcf28c8ff.
4. Whether a non-bypass identity is refused is stated as not verified. No non-admin identity exists to test with, since the machine account is deferred. The owner, as bypass actor, may check through the ruleset's insights or evaluate view that a tag update is evaluated as expected; otherwise this is stated as "not verified".

## Related Tickets
- TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION
- TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION (split from)
- TCK-20261031-SDLC-R0-INVENTORY-AND-BASELINE-TAGS (made the tags)

## Related Docs
- docs/plans/agent_infrastructure/SDLC_DECISION_RECORD.md
- docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md

## Related Stored Artifacts
- agent-working/stored_artifacts/sdlc-phase-0/ruleset_14220945_export.jsonl (old before-state, pre-transfer)

## Related Code Areas
- GitHub repository rulesets (owner-applied)

## Assumptions / Open Questions
- Owner condition #715 6528807751: credential details stay out of committed files, tickets and public comments.
- A seat prepares the steps; only the owner applies a ruleset change.
- The bypass-actor types available to an organization repo differ from those for a personal repo. Read what the API offers; don't assume the plan's personal-repo list.
- Timing: the owner ordered this epic's work after the ticket view epic (P3c and backlog view).

## Implementation Notes
The owner wanted this applied now. Under RPG-first (#715 6911759453), lead-planner did items 1 and 2 itself rather than spend a seat; agent-working-planner records them here.

**Item 1, before-state** (lead-planner, read fresh 2026-11-16 at main 18af29f5e; agent-working-planner re-read the same day and it matches):
- One ruleset: 14220945 `protect_branches`, target branch, enforcement active, include `~DEFAULT_BRANCH`, exclude none.
- Its rules: deletion, non_fast_forward, update, required_status_checks.
- Its bypass: actor type RepositoryRole, actor_id 5 (admin), mode always.
- No tag ruleset exists.
- Tags, from `git ls-remote --tags origin 'baseline/*'`: the four tag objects match AC3 exactly, and all four peel to 6fdfdf5556548105e28ab370832f36bc96241561.

**Item 2, prepared, not run** (lead-planner): a new ruleset `protect_baseline_tags`, target tag, enforcement active, include `refs/tags/baseline/sdlc-*`, rules deletion, update and non_fast_forward, with the same bypass (RepositoryRole 5, always). The branch ruleset is untouched. The JSON is held in lead-planner's scratchpad; the owner applies it with `gh api` POST (item 3).

**Item 3, applied:** the owner applied it on 2026-11-16, logged by lead-planner at #715 6917273988. The new ruleset is 27374064 `protect_baseline_tags`.

**Item 4, after-state** (lead-planner; agent-working-planner re-read it the same day and it matches):
- Two rulesets now exist:
  - 27374064 `protect_baseline_tags`: target tag, active, include `refs/tags/baseline/sdlc-*`, rules deletion, update and non_fast_forward, bypass RepositoryRole 5 always;
  - 14220945 `protect_branches`: unchanged in its conditions, its rules (deletion, non_fast_forward, update, required_status_checks) and its bypass.
- AC3: all four tags are unchanged on both SHAs. The tag objects are 643b26a4…, 7924b36e…, 060f25e4… and 91ef2ac8…, as listed in AC3, and each peels to 6fdfdf5556548105e28ab370832f36bc96241561.
- AC4: not verified. No non-admin identity exists to test with, since the machine account is deferred.

## Test Summary
No code changed. Verification was by read:
- `gh api .../rulesets` and `.../rulesets/<id>`, before and after;
- `git ls-remote --tags origin 'baseline/*'`, before and after.

AC1, AC2 and AC3 hold. AC4 is stated as not verified.

## Files Changed
- This ticket only.
- The change itself is a GitHub repository setting (ruleset 27374064), which the owner applied.

## Completion Summary
The four frozen SDLC baseline tags are now protected against deletion, update and non-fast-forward by tag ruleset 27374064. The admin role keeps its bypass, and the branch ruleset is unchanged.

lead-planner did the before-read, prepared the ruleset and did the after-read. The owner applied it (#715 6917273988). agent-working-planner recorded the work and re-verified both reads.

Gap stated: AC4, whether a non-bypass identity is refused, is not verified until a non-admin identity exists (deferred with the machine account).
