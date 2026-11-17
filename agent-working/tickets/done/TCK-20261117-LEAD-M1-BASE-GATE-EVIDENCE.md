---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261117-LEAD-M1-BASE-GATE-EVIDENCE
phase: done
date: 2026-11-17
tags: [governance]
---

# TCK-20261117-LEAD-M1-BASE-GATE-EVIDENCE

## Title
The rpg gate reports behind the Milestone 1 re-baseline are kept on main, byte for byte, together with the lead's own monitoring rows

## Status
DONE

## Tier
hotfix

## Type
chore

## Priority
P2

## Request Summary
On 2026-11-16 the owner approved re-baselining the rpg gate's M0 reference to M1-base (#715 6920465555, how 6920528237). The gate's report JSON lives only as GitHub Actions artifacts, which expire. lead-planner copied the artifacts byte for byte onto backup branch `lead-m1base-gate-report` (S2 pushes 6920490049 and 6922864219), but that branch had no PR. On 2026-11-17 the owner answered "Start it now (Recommended)" (6934480106): fold the branch and the lead's uncommitted W47 monitoring rows into one PR.

## Scope
- Land `agent-working/lead/evidence/rpg-gate-report-9c398a068.json`. This is run 43840618903's report on M1-base 9c398a068, sha256 6572340e9832331d2cfb0da89049ba48b08617d1bee9eb8df2fb29ada4d0a1ac.
- Land `agent-working/lead/evidence/rpg-gate-report-e72270894.json` and `rpg-gate-candidate-e72270894.json`. These are run 43895014837's report and baseline candidate on main e72270894; the run had no ref input and came back green.
- Carry the lead's uncommitted W47 monitoring rows from the main checkout.

## Out of Scope
- Running the re-baseline itself, which belongs to the rpg gate's owner on u24.
- Any change to the gate workflow or `rpg_gate_baseline.py`.

## Acceptance Criteria
1. Each evidence file is byte-equal to its artifact. Check: the branch commits 76ac700fa and 0db6b6954 are unchanged, and the sha256 values match the ones in the S2 log entries.
2. The carried monitoring shards parse as JSON lines, and none of their rows duplicates one already on main.
3. The ticket's frontmatter is valid.

## Related Tickets
- TCK-20261109-MILESTONE-1-KINDS-BY-PROPERTIES-EPIC
- TCK-20261116-LEAD-BOARD-SIXTH-PASS (#945)

## Related Docs
None changed.

## Related Stored Artifacts
None.

## Related Code Areas
None.

## Assumptions / Open Questions
- The evidence is stored as `.json` under `agent-working/lead/evidence/`, not `stored_artifacts/`, so the gitignore rule that drops `stored_artifacts` JSON does not apply. The files are tracked on the branch.

## Implementation Notes
Hand-orchestrated hotfix by lead-planner on branch `lead-m1base-gate-report` (worktree `.claude/worktrees/lead-m1base-gate-report`), with origin/main f4ac858f9 merged in.

## Test Summary
- `python3 tools/validate_frontmatter.py` on this ticket.
- The monitoring shards parse as JSON lines.

## Files Changed
Three evidence JSON files, this ticket, `docs/REGISTRY.yaml`, monitoring shards.

## Completion Summary
The gate evidence for the M1 re-baseline is on main. No code, docs or tests changed.
