---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261119-FILED-TICKETS-ARE-SCANNED-FOR-OVERLAP-WITH-OPEN-TODOS
artifact_type: investigation
tags: [delivery]
---

# investigation — TCK-20261119-FILED-TICKETS-ARE-SCANNED-FOR-OVERLAP-WITH-OPEN-TODOS

Measured on origin/main 5bedb5ff0: 225 open tickets (todos/ + inprogress/), 151 filed in the 21 days before 2026-11-19. Scripts were run from the scratchpad; the 20-pair label sample is `/data/vboxuser/aw-dryrun/overlap_sample20.md`.

| item | finding |
|---|---|
| Raw score | grows with the query's length: an "unrelated" sampled pair scored 83.0 raw (above the fixture's 81.5); so the check uses q = matched IDF weight (plus 10 per shared code area) / the draft's own total IDF weight |
| Positive controls | SLOW-CORPUS-GRADE-PINS vs SIMQ-ANCHOR-REDS...BISECT: raw 81.5, q 0.388, rank 1; vs SIMQ-V1-HELD-ROWS: raw 58.7 (ids stripped), q 0.279, rank 2; CLEAR-TARGET pair 0.491 |
| Self-citation | stripping `TCK-` ids from title and summary changes HELD-ROWS from 61.8 to 58.7 raw; BISECT unchanged |
| Hook reach (357 ticket files first added in 21 days) | done_checker_static: at most the closed ones, none of the open ones, only if run by hand; validate_frontmatter: called only from done_checker_static and the registry tools, never at commit or in CI; pre-commit: two hooks (src ratchet, uv-lock), none installed in this clone; push advisory: every ticket pushed by a harness session. 357 of 357 arrived in a squash-merged PR; 295 (83%) with a pr_render-shaped title |
| Labels (20 pairs, agent-working-planner and rpg-planner-ubuntu) | 10 useful (DUP or RELATED), 10 unrelated; about 50% in every q band (3 of 7, 4 of 7, 3 of 6); Wilson 95% roughly 28 to 72% |
| Raw floor 35 | drops 4 useful rows (including the owner's inn-meal pair, q 0.259, raw 25) and 5 unrelated: rejected |
| Epic-sibling exemption | only 29 of 225 tickets are in an epic family; the M1 children are declared in the body ("Child of ..."), siblings can be truly related: rejected |
| Caps (no exemption, q >= 0.25) | tickets with a line stay 71/151 (47%) at every cap; lines 71 (cap 1), 120 (cap 2), 154 (cap 3), 311 (none); cap 1 loses control row 1; cap 2 keeps all five controls |
| Decision | q >= 0.25, no raw floor, no exemption, ids stripped, top 2 uncited hits, one summary line per ticket; the 47% is the price of the owner-named inn-meal miss |
| Not measured | how many of the 62 hand-titled PRs went through pr_render; precision per band beyond n=20; the effect on citation rates (the `--report --since` mode measures it prospectively) |
