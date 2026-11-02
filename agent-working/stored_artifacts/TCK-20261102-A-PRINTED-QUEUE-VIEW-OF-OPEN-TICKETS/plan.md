---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261102-A-PRINTED-QUEUE-VIEW-OF-OPEN-TICKETS
artifact_type: plan
phase: done
date: 2026-11-02
tags: [delivery]
---

# Plan

1. **`tools/delivery/ticket_queue.py`** (new, read-only). `python3 tools/delivery/ticket_queue.py [--ref origin/main] [--worktree] [--json] [--no-gh]`. Output header: ref and sha (or `worktree`), ticket count, warnings. Exit 0 unless the tool itself fails.
   - **Collect:** default `git ls-tree -r --name-only <ref> agent-working/tickets/todos agent-working/tickets/inprogress` and `git show <ref>:<path>` through an injectable `run_command`; `--worktree` reads the files. One row per path (AC1). A ticket ID with files in more than one status folder is flagged `two-folders`, not resolved.
   - **Row fields:** `id, folder, layer, priority, tier, status` (first token), `order, blocked, parked, flight, epic`.
   - **order:** optional `## Order Ref` body section (first line = a §12.5 short name). The position is the 1-based index in the roadmap's LAST order line (`... the order is A → B → ... .` in §12.5, parsed from the roadmap read at the same ref). Name not in the line: `stale-ref`; no section: `unknown`; line unparseable (no match or fewer than 3 steps): every row `unknown` and one warning. No fallback guess.
   - **blocked:** only when Status is BLOCKED; `on:` = ticket IDs found on the Status line, else `on: unknown`.
   - **parked:** `yes path:line` only for three patterns (a `## Parked`/`## Paused` heading; a line starting `**Paused (owner,`; a line starting `**Parked by explicit user decision`). The word elsewhere = `mention` (never counted as parked).
   - **flight:** `pr #N` from `gh pr list --state open --json number,title,files,commits` when changed files or commit subjects name the ID; `claim <comment id>` (latest) from #634 comments naming the ID, labelled as a claim. `gh` missing or failing: `unknown` + warning. The word "running" is never printed.
   - **epic:** EPIC_SCOPED status or tier epic rows are marked `epic` and left out of work counts.
   - **Summary:** counts per state with `unknown` counts, P1 by status, by tier and by layer. `--json` emits the same data (rows + summary + warnings).
   - `SEQUENCE.md`: ignored; only `folder` shows.
2. **`tests/tools/test_ticket_queue.py`** (new; split-routed, so a PR note tells rpg): fixtures for `OPEN (prose ...)`, BLOCKED with and without an ID, `previously BLOCKED` prose in an OPEN status (reads OPEN), the bold `ENV-06 ... parked` line (not yes), `**Paused (owner,` (yes), `Parked time:` (mention), order in-line / `stale-ref` / none, an unparseable roadmap (all unknown + warning), the real §12.5 line (last-match rule; positions asserted), `gh` unavailable (flight unknown + warning), two-folders flag, tree byte-identical before and after, default run reads no working-tree ticket (runner-only fixture), `--json` equals the text data.
3. **`docs/ai/ticket-lifecycle.md`**: a short section naming the command and the optional `## Order Ref` section. `make knowledge-index-update`.
4. **Real-tree run** recorded in `investigation.md`, with each `parked: yes` hand-checked (AC6).
5. Not touched: `roadmap.md`, rpg tickets' Order Ref, `docs/REGISTRY.yaml` entries for the tool, any validation of `## Order Ref` at close, the dashboard Tickets view.

## Designer amendments (agent-working-designer-u24, all folded in)
- **A. Order line scope.** The search is limited to §12.5, from its `### 12.5` heading to the next heading of level 3 or higher. The header prints the parsed order and its `path:line`. One warning: if any `→` or the word "Amended" appears in the section AFTER the last match, the order may be superseded (positions still print). Today's trailing "F4 lands as soon as it is ready" sentence has neither, so no warning fires.
- **B. `gh` limits.** `gh pr list --limit 1000`; warn if the result reaches the limit. `files` caps at 100 per PR: warn for any PR at the cap, naming it. #634 is read with `gh api --paginate`.
- **C. Flight labels.** `pr #N closes` when the PR's files include `done/<ID>.md`, else `pr #N touches` (changed file or commit subject names the ID); the summary counts the two separately. #634 comments naming the ID print `#634 comment <id>`, not "claim", unless a real claim form matches (the ticket's "labelled as a claim" wording is narrowed; noted in the ticket).
- **D. Real-roadmap test.** Exact positions are asserted on a verbatim fixture copy of today's roadmap line (§12.5, line 1264). The real-file test asserts only that §12.5 parses to at least 3 steps; its failure message names the tool and says the view degrades to `unknown`. The PR says an rpg roadmap edit can fail this test, for the designer to weigh.
- Non-blocking, also done: the header prints the commit date beside the sha (the tool does not fetch, so origin/main may be stale); only `/TCK-*.md` paths are listed (ls-tree also returns .gitkeep, SEQUENCE.md, INDEX.md); fenced lines are skipped in the parked scan; the doc says F4's position is nominal (conditional), and that a lifted pause left in the text still reads `yes` (the `path:line` is how to check).

- Added after the AC6 hand check: a fourth `yes` pattern, a line starting `**Parked**` (it was a real park read as `mention`). See investigation.md.

Reviewer: agent-working-designer-u24 reviews this plan.md before Implement.
