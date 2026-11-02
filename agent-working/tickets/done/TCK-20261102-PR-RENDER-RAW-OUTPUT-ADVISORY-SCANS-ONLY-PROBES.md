---
status: historical
layer: ai
authority: P1
audience: agent
ticket_id: TCK-20261102-PR-RENDER-RAW-OUTPUT-ADVISORY-SCANS-ONLY-PROBES
phase: done
date: 2026-11-02
tags: [delivery]
---

# TCK-20261102-PR-RENDER-RAW-OUTPUT-ADVISORY-SCANS-ONLY-PROBES

## Title
pr_render's raw-output advisory scans a ticket's whole stored_artifacts folder, not only probes/

## Status
DONE

## Tier
hotfix

## Type
bug

## Priority
P2

## Request Summary
Owner-directed through lead-planner-u24 (2026-11-02). `raw_probe_warning` (TCK-20261009-PR-RENDER-RAW-PROBE-OUTPUT-ADVISORY) only looks under `agent-working/stored_artifacts/**/probes/`. PR #828 at 9716c6785 adds 287 stored-artifact files, 4.65 MiB, all under `evidence/` or at the folder top, so nothing warned and the owner caught it by reading the PR. The owner has ruled #828 trims at re-sync (#715 6573916118); this ticket is the tool gap only.

Measured:
- **#828 by type (all 287 files, two tickets):** .jsonl 62 files 2.54 MB, .json 80 files 1.64 MB, .stdout 7, .done 18; versus .py 52, .sh 30, .txt 26, .md 12 (0.62 MB together). So the existing extension rule counts 4.26 MB as raw and would have warned once the path limit is gone. Scripts and summaries aren't the weight, so the extension filter still fits.
- **Noise replay on origin/main, per ticket folder (a stand-in: PRs were not replayed):** of 1968 folders, 11 exceed 200 KB of raw output under the wider rule, 5 exceed 500 KB and 1 exceeds 1 MB; 0 exceed it under today's probes/-only rule. 5 of the 11 are visual-assets folders whose raw bytes may be legitimate images; report-only, so a second look there costs little.
- **Required artifacts:** plan.md, investigation.md and test_plan.md are `.md`, so the extension filter already leaves them out. No separate "required file" list is needed.
- **Discovery:** `discover_changed_files` is git-based, so `gh pr view --json files`'s 100-file cap doesn't apply. But it is two-dot (`base..HEAD`), a tree diff: on a branch behind main it also lists files only main changed, and the advisory would count those. Today's narrow scope hides this; the wider scope makes it matter. Its docstring records the other caller, the ticketless file summary.

## Scope
- `tools/delivery/pr_render.py`: `raw_probe_warning` scans every changed file under `agent-working/stored_artifacts/`, not only `/probes/`. Same 200 KB threshold and same `_PROBE_NON_RAW_SUFFIXES` filter. Rename the function and constants for what they now do. Report-only.
- The advisory gets the three-dot list (`git diff --name-only base...HEAD`). `discover_governing_files` already makes that call, so reuse it or split a helper; don't change `discover_changed_files`'s form for the ticketless summary.
- The message says the scope (the whole folder), keeps the largest-5 list, and adds the total file count and total bytes for stored_artifacts in the PR, so a file-heavy PR shows its size.
- Tests in `tests/tools/test_delivery_pr_render.py`, in the agent-working part of this split file.
- `docs/guides/delivery_process.md` (the PR-lifecycle note about the 200 KB probes advisory): name the new scope.

## Out of Scope
- #828's trim (rpg, ruled at #715 6573916118) and pruning existing files.
- A blocking gate or CI job. A file-count trigger: #828 fires on bytes, so one isn't needed yet.
- Checking whether a raw file is cited.
- The `.gitignore` rule on `stored_artifacts/**/*.json`: #828's 80 `.json` files were added past it. Worth a look by rpg-planner on the trim; not changed here.
- `discover_changed_files`'s two-dot form for the ticketless summary.

## Acceptance Criteria
1. More than 200 KB of raw output under `evidence/`, at a ticket folder's top, or in any other subfolder warns. Under `probes/` it still warns.
2. `.py`, `.sh`, `.md` and `.txt` don't count toward the threshold, but do count in the printed totals. A deleted file counts for nothing.
3. A file only main changed (branch behind main) isn't counted (fixture with a fake runner on the three-dot call).
4. At or under the threshold: no warning. Rendering and exit status are otherwise unchanged.
5. The `investigation` note in Implementation Notes records one real replay against #828's head 9716c6785, or a later head if that one is gone: the warning fires and the numbers match.
6. Scoped run: `pytest tests/tools/test_delivery_pr_render.py -q` is green.

## Related Tickets
- TCK-20261009-PR-RENDER-RAW-PROBE-OUTPUT-ADVISORY (the rule this widens)
- TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS (#828, 4.21 MiB)
- TCK-20261102-A-PRINTED-QUEUE-VIEW-OF-OPEN-TICKETS (same batch if the owner agrees)

## Related Docs
- `docs/guides/delivery_process.md`

## Related Stored Artifacts
None.

## Related Code Areas
- `tools/delivery/pr_render.py` (agent-working)
- `tests/tools/test_delivery_pr_render.py` (split rpg/agent-working)

## Assumptions / Open Questions
- 200 KB was chosen for one probe batch and is kept. The replay says 11 of 1968 folders; raise it only if real PRs show noise.

## Implementation Notes
`raw_probe_warning` is now `raw_output_warning` (constants `RAW_OUTPUT_WARN_BYTES`, `_NON_RAW_SUFFIXES`, `_RAW_OUTPUT_TOP`). It scans every changed file under `agent-working/stored_artifacts/` and `render` feeds it `discover_governing_files`' three-dot list (reused, `discover_changed_files` is unchanged). The message names the scope, keeps the largest 5, and adds the total stored_artifacts file count and size (scripts and summaries count in the totals, not the threshold; a deleted file counts for nothing).
Investigation note, replay against #828's head 9716c6785 (stored_artifacts files extracted by `git archive`, three-dot list against origin/main): 287 files, 4765 KB in the totals (4.65 MiB, as measured). The warning fires: 167 raw files, 4156 KB, largest `TCK-20261031-A-PAIR-RE-FORMS-AND-LEAVES-A-GROUP-EVERY-TWO-TICKS/evidence/f3_remeasure/traces/tier2/crowded_frontier_s43.jsonl` (424 KB). The old probes/-only rule found 0 files in that PR.

## Test Summary
`pytest tests/tools/test_delivery_pr_render.py -q -p no:randomly`: 90 passed (new: anywhere under stored_artifacts warns, four locations; scripts/summaries out of the threshold but in the totals; a deleted file counts for nothing; a file only main changed is not counted via the three-dot call; the old threshold and render tests renamed).

## Files Changed
tools/delivery/pr_render.py; tests/tools/test_delivery_pr_render.py; docs/guides/delivery_process.md.

## Completion Summary
pr_render's raw-output advisory now covers the whole stored_artifacts folder from the three-dot diff, and the replay against #828 fires it. #828's trim, a blocking gate and the .gitignore rule are untouched.
