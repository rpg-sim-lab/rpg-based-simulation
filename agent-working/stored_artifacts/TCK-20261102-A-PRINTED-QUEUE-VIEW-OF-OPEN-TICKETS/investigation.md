---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261102-A-PRINTED-QUEUE-VIEW-OF-OPEN-TICKETS
artifact_type: investigation
phase: done
date: 2026-11-02
tags: [delivery]
---

# Investigation

## Findings (measured on this checkout, origin/main + the seat's ticket; 123 tickets = todos/ and inprogress/)
- Status first token: OPEN 100, EPIC_SCOPED 9, BLOCKED 8, INPROGRESS 6 (the 6 in `inprogress/` are included in the 123).
- BLOCKED: 1 of 8 names a ticket ID on the Status line (CALAMITY-INTENSITY: `BLOCKED (on TCK-20260914-LAIR-...; ...)`); the other 7 read `on: unknown`.
- Parked: a strict line pattern (heading `## Parked|Paused`, or a line starting `**Paused (owner,`, or `**Parked by explicit user decision`) hits 9 lines in 7 tickets by my script (the designer counts 7 lines in 7 tickets on origin/main, whose tree has one ticket fewer); the count is reconciled in the AC6 run. The word `parked` appears in 16 other tickets: those are `mention`.
- `## Order Ref`: 0 tickets carry it today (the section is new and optional); rpg-planner fills it separately.
- Roadmap §12.5 (`docs/plans/systemic_world/roadmap.md` line ~1253): the order is stated in prose, amended twice. The LAST sentence of the form `... the order is HUNGER B → A → F4 → F3 → precedence → N14 → A' → nav → D80C → decision 73 → the items.` is the current line (steps split on `→`, no `.` inside a step). An earlier sentence `The order is then HUNGER B → A → F4 → F3 → N14 → A' → nav → decision 73 → the items.` is superseded; taking the first match would be wrong, so the rule is "last match".
- Flight: no ticket field holds it. Sources are open PRs (`gh pr list`: changed files or commit subjects naming the ID) and #634 claim comments (claims are never released, so shown only as `claim <comment id>`).
- Reuse: `generate_registry.parse_body_section` and `_strip_frontmatter`, `validate_frontmatter.extract_frontmatter`, `ticket_field_values` enums. Git reads follow `pr_render.default_run_command`'s pattern (an injectable runner, so tests need no git or gh).

## Design decisions
1. Default source is `git ls-tree`/`git show origin/main:<path>` via an injected runner: no working-tree read, so AC2 holds by construction. `--worktree` globs the tree.
2. Order ref lookup is exact (case-insensitive, whitespace-normalised) against the step names of the last order line. No fuzzy or text match anywhere (AC7).
3. `parked: yes` carries `path:line`. The CALAMITY-INTENSITY ticket's bold `ENV-06 ... parked` line matches none of the three patterns, but the ticket itself reads `yes` through its own Completion Summary line (`**Parked by explicit user decision`, ~line 327). The AC6 hand-check judges that row. A pause later lifted but left in the text still reads `yes`; `path:line` is how a reader checks.
4. Status uses the first token with `*`, backticks, `:` `,` `;` and `(` stripped; `previously BLOCKED` in prose inside OPEN is not read because only the first token counts.
5. Everything is report-only: exit 0 unless the tool fails; a `gh` failure gives `flight: unknown` and a warning.

## Real-tree run (AC6)
Run: `python3 tools/delivery/ticket_queue.py --no-gh` and `--json` at origin/main `ca9ebe7c6` (127 ticket files: 116 work rows + 11 epic tracking rows; 0 in two folders; 6 BLOCKED rows name no dependency; order positioned 0 because no ticket carries `## Order Ref` yet). With `gh`: PR #828 hits the 100-file cap and is warned; flight counts closes 1, touches 1, none 114.
Parked, each `yes` row read on the real file line:
- 8 `yes` rows, 0 false positives. CALAMITY-INTENSITY (line 327) and LAIR-REGION-TRAUMA (line 281): the ticket's own Completion Summary says "Parked by explicit user decision". EAT-BESIDE-THE-INN (line 123): heading `## Parked (owner ruling 2026-10-08)`. SPAWN-AND-DERIVATION (line 151): `**Parked**, per the user's 2026-10-02 direction`. Four perf/combat tickets: `**Paused (owner, #715 ..., recorded 2026-11-01)`.
- The fourth pattern (`^**Parked**`) was added after this hand check: the first run with three patterns left SPAWN-AND-DERIVATION as `mention` (a real park). The designer's count of 7 lines in 7 tickets matches the three-pattern result; my earlier prototype counted 9 lines because it also matched `**Parked here` (CALAMITY line 214) and the SPAWN line.
- `mention` rows (9): by hand, 3 are real parks the narrow patterns miss (IMPLEMENT-TICKET-NATIVE-PORT line 59 `- **Parked 2026-10-18 (owner decision ...`, STANDARD-SLOW-REGRESSION line 31 `**Deliberately deprioritised and parked`, POSITION-SWAP line 107 `Parked by owner_decision_memo.md row 7.`), 1 is partial (tuning thresholds parked, not the ticket), 5 are not parks (a ticket ID containing PARKED, `Parked time:`, "remains parked" checklist text, a moved-from-parked-feature note, a backlog line). That is the safe direction: a miss reads `mention`, never a wrong `yes`.
- False-positive count for `yes`: 0 of 8. False negatives read as `mention`: 3.
