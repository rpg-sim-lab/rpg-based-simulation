---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261102-A-PRINTED-QUEUE-VIEW-OF-OPEN-TICKETS
artifact_type: test_plan
phase: done
date: 2026-11-02
tags: [delivery]
---

# Test plan

`tests/tools/test_ticket_queue.py`, `pytest tests/tools/test_ticket_queue.py -q -p no:randomly`. All git/gh calls go through the injected runner (no network, no repo state). Cases map to the ACs:
- AC1: every path under todos/ and inprogress/ once; header names ref and sha; a two-folder ID is flagged.
- AC2: a tmp tree is hashed before and after a `--worktree` and a default run (identical); the default run with the working tree emptied still lists the runner's tickets.
- AC3: status fixtures (`OPEN (prose ...)`, BLOCKED with/without an ID, `previously BLOCKED` inside OPEN), parked fixtures (`**Paused (owner,` yes with `path:line`; bold ENV-06 line not yes; `Parked time:` mention), mention never counted as parked.
- AC4: runner raising/failing for `gh`: flight `unknown`, warning printed, view still prints, exit 0.
- AC5: summary has `unknown` counts and P1 by status/tier/layer; `--json` equals the text data.
- AC7: a verbatim fixture copy of today's roadmap line 1264 parses to the 11 steps with exact positions; the real roadmap file is asserted only to parse to at least 3 steps (failure message names the tool and the `unknown` degradation); a superseded-looking trailing `→` or "Amended" after the last match warns; in-line ref, `stale-ref`, no ref; a roadmap with no order line gives all `unknown` plus one warning; the superseded earlier sentence is not used.
- Epic rows are marked and excluded from work counts.
- AC6 is the hand-checked real-tree run in investigation.md.
- Flight: `pr #N closes` (done/ file in the PR) vs `pr #N touches`, counted separately; the `--limit` reached and a 100-file PR each warn; #634 comments print `#634 comment <id>`.
- Collect: only `/TCK-*.md` paths (a .gitkeep, SEQUENCE.md and INDEX.md in the listing are skipped); header carries the commit date; fenced lines are not parked.
