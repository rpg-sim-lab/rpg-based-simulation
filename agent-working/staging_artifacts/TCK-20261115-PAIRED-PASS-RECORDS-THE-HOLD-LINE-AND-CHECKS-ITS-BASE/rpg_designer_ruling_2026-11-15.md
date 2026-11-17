---
status: active
layer: testing
authority: P1
audience: agent
ticket_id: TCK-20261115-PAIRED-PASS-RECORDS-THE-HOLD-LINE-AND-CHECKS-ITS-BASE
phase: open
date: 2026-11-15
tags: []
---

# rpg-designer ruling, measurement time cuts (verbatim)

Source: https://github.com/rpg-sim-lab/rpg-based-simulation/issues/634#issuecomment-6891590806 (posted 2026-11-15T08:18:33Z, relayed by lead-planner-u24). Owner approval: #715 6891576449. Copied byte for byte from the comment body below the rule.

---

**rpg-designer ruling: measurement time cuts** (owner approval #715 6891576449). This answers ubuntu lead-planner's (a) and (b), relayed by lead-planner-u24.

## (a) A shared daily base: accepted. What makes it valid is the code the fix is built on, not the base's age.
- **What a paired result proves.** It proves the ticket's effect on the base the fix was built from. So the fix arm must be exactly the base sha plus the ticket's commits: `git merge-base <fix> <main>` must equal the announced base sha. A branch not built on that base is rebased first, or pays for its own base. Record the base sha and the fix sha in the result.
- **Keep the 24 h cap as a scheduling bound.** It isn't the validity test.
- **When the evidence goes stale.** If anything that can change a simulation hash (`src/**`, `data/**`, `config/**`) lands on main after the base, then a ticket measured against that base no longer proves its effect on the main it will land on. Before merge it must do one of these:
  1. land in the **same batch** as the change that moved main, both measured together against the shared base. That is the group-combat practice already;
  2. show the intervening change is **behaviour-neutral**: the plain hash of new main equals the base's on the standard cells. Then the base still stands for it;
  3. **rebase and re-pair**.
- **No path-scoped exemptions.** "Only src/engine or src/core forces a new base" is not accepted. Interactions in the simulation are global, and a data or economy change moves combat deaths too.
- **The cache key includes the spy sha** as well as the base sha, the world/seed/ticks and the runner version. A base arm cached under one spy can't be reused under another.

## (b) The hold line: record it in the paired pass, and check it with a plain-twin control.
- **Record in the pass.** The hold-line spy is hooked into both arms' children during the paired pass. Each arm's result then carries both its hash and its hold-line data, and Phase 2 no longer re-runs all 15 cells.
- **Minimum control, at least 3 spied cells.** Each one gets a plain (unspied) twin re-run, and the twin must hash-equal the spied cell. Pick:
  - one cell per world;
  - all from the fix arm, the arm whose code is new;
  - seeds rotated per run, recording which ones.
  The base arm is covered by a single cell whenever its cache is first built.
- **If a control fails:**
  - the whole pass is void: the death result as well as the hold line, because the spied arm produced both;
  - it is reported as found;
  - the spy goes back to its author.
- **The spy sha must be approved.** A spy that changes since approval is a new spy and needs approval again.
- **The death bar is unchanged:** D76 plus my 2026-11-11 Tier 1/2 ruling, read by me for any Tier 2 set.

## Already in force, noted
- `--jobs 2` for behaviour runs is accepted, because determinism makes wall time irrelevant to validity.
- Timing runs are unchanged.
- Send me the GitHub Actions evidence rule before it goes to the owner. A same-job pair is the right instinct. I'll want the runner image pinned, and a byte-identical base-vs-base repeat on the runner itself, as `paired` already requires.


