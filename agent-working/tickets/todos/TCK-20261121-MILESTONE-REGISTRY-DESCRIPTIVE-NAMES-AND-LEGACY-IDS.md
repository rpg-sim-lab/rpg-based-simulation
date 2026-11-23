---
status: active
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261121-MILESTONE-REGISTRY-DESCRIPTIVE-NAMES-AND-LEGACY-IDS
phase: open
date: 2026-11-21
tags: []
---

# TCK-20261121-MILESTONE-REGISTRY-DESCRIPTIVE-NAMES-AND-LEGACY-IDS

## Title
Add an append-only milestone registry that maps each descriptive milestone name to its legacy short id, and a lint against a bare `M<n>` in new tickets

## Status
OPEN

## Tier
standard

## Type
feature

## Priority
P2

## Request Summary
Owner decision on #715 (comment 7064089876, relayed by lead-planner-u24 and read by lead-planner): milestones get descriptive names. A bare "M1" means four things in docs/plans: the systemic world roadmap §12 Milestone 1, the closed rpg_design_roadmap M1-M9, the HUD roadmap and the live-map roadmap. The systemic world roadmap §12 Milestone 1 (base 9c398a068) is now `systemic_foundation`.

Option 1 (owner): the gate keeps its stored baseline label `M1` until this milestone ends. Existing baselines are never edited. From the next milestone, gate labels and docs use descriptive names directly. Docs, tickets, PRs and #715 records write "systemic_foundation (M1)" from now on.

The request: a small milestone registry, append-only like `registries/layer_registry.jsonl`. One row per milestone: name, legacy short id, roadmap file and section, base commit, start and end dates, status. Seed `systemic_foundation` <-> `M1`, and disambiguate the other roadmaps' M-numbers. Optional: a lint so new tickets do not write a bare `M<n>`.

Routing: #715 says the registry goes to agent-working-designer; the u24 relay named agent-working-planner. Planner files it (agent-working domain, planner files tickets); agent-working-designer reviews. Lead-planner is told.

## Scope
1. `registries/milestone_registry.jsonl`, append-only, one row per milestone with: `name`, `legacy_id`, `roadmap` (file + section), `base_commit`, `start_date`, `end_date` (null while open), `status` (open | closed).
2. A small CLI `tools/milestone_registry.py` with `list` and `add`, modelled on `tools/layer_registry.py` (read it first, reuse its append-only and duplicate-name checks). `add` refuses a duplicate name and refuses to rewrite a row; closing a milestone is a new row or an `end` subcommand that appends, decided in the plan.
3. A lookup function `legacy_id -> name` for the gate's baseline label, scoped to the roadmap that owns it, since four roadmaps use `M1`. The gate itself keeps its `M1` label; this ticket adds the lookup only and edits no baseline.
4. Seed rows: `systemic_foundation` (legacy `M1`, systemic world roadmap §12, base 9c398a068, open); rows for the closed rpg_design_roadmap M1-M9, the HUD roadmap milestones and the live-map roadmap milestones with their real roadmap file and section (read the roadmaps; take the names from them or leave a proposed descriptive name flagged for the roadmap owner, never invent a silent one).
5. Optional, advisory only (report, never fail): a lint over tickets filed after the landing date that flags a bare `M<n>` not accompanied by a registered descriptive name. Reuse the existing frontmatter or ticket-field validator pattern; report ran/skipped/errored status.
6. One doc line in the registry guidance (find where `layer_registry` is documented and add the milestone registry beside it).

## Out of Scope
- Editing any stored gate baseline or the gate's `M1` label.
- Rewording the roadmaps; roadmap wording goes to each roadmap's owner (#715 7064089876).
- A blocking lint.
- Any `src/` change.

## Acceptance Criteria
- The registry file validates: unique names, required fields, dates in order, status in the enum; append-only is enforced by the tool.
- `systemic_foundation` <-> `M1` resolves; `M1` scoped to another roadmap resolves to that roadmap's milestone, not to `systemic_foundation`.
- Tests under `tests/tools/` cover add, duplicate refusal, lookup with the same legacy id on two roadmaps, and an unknown id.
- If the lint is built: advisory, with fixtures for a bare `M1`, a `systemic_foundation (M1)` citation and a ticket dated before the landing date.
- No stored baseline or gate label changed (diff check).

## Related Tickets
- TCK-20261119-FILED-TICKETS-ARE-SCANNED-FOR-OVERLAP-WITH-OPEN-TODOS (advisory-check shape to reuse)

## Related Docs
- registries/layer_registry.jsonl and tools/layer_registry.py (the append-only shape)
- docs/plans (systemic_world roadmap §12; rpg_design_roadmap; hud_delivery_roadmap; live-map roadmap)

## Related Stored Artifacts
None.

## Related Code Areas
registries/, tools/, tests/tools/

## Assumptions / Open Questions
- Which tool reads the gate's `M1` label is not yet located; the plan names it before any code change. If it cannot take a lookup without editing baselines, report to the planner.
- Roadmap owners confirm the descriptive names for the non-systemic M-numbers; until then those rows carry a `proposed` flag or are left out.

## Implementation Notes
Hold until the owner or lead-planner dispatches; it does not compete for systemic_foundation time (lead-planner relay).

## Test Summary
Not started.

## Files Changed
None yet.

## Completion Summary
Not started.
