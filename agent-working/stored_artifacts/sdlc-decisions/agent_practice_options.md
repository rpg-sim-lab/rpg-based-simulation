---
content_type: doc
status: historical
layer: ai
authority: P2
audience: agent
tags: [ai, governance, process-improvement]
---

# Agent practice: quick fixes, comments, markdown. Options for the owner

Study by agent-working-designer, 2026-11-16, measured at origin/main db6b4579d. **Decided by the owner on #715 6913007039: option A on all three points** (1A: ticket id plus a report-only flag, scoped to correctness and hard-rule fixes; 2A: keep why and pointer comments, trim narration on touch; 3A: count reads first). The page is kept as the decision's evidence and is not updated after the decision. Any edit to CLAUDE.md or the ticket workflow remains the owner's direct yes. Request: the owner's three points from the talk "All Code Is Slop (Except Mine)" (Lauren Tan; the local summary `tmp/youtube-summary.md` is unverified and I did not watch the talk), and "study best practice, don't guess".

## What the talk summary actually says, and what it does not

The summary I have says: trust comes from architecture, then deterministic rules (lint, types, tests), then runtime verification, and last natural-language instructions; "if an expectation can be enforced in code, prefer that over repeating it in prose"; agents copy patterns they find, so workarounds spread; fix recurring agent mistakes by changing architecture, tooling or tests. It does NOT contain the three claims as the owner relayed them (drop explanatory comments, delete 99.9% of comments, write no markdown). Those come from the owner's memory of the talk, so treat them as unverified. The summary's own principle supports a machine check over a prose rule, and that shapes every option below.

## What the sources say (read from the papers, not from search summaries)

| Source | Result | Limits the authors state or that I found |
|---|---|---|
| Mehtiyev and Assunção, [Beyond Resolution Rates, arXiv:2604.02547](https://arxiv.org/abs/2604.02547): 9,374 trajectories, 19 agents, 500 SWE-bench Verified tasks | Of 12 tasks no agent solved, "in 10 of 12 tasks, the failure traces back to architectural judgment": the agent patches the symptom (caller, consumer, display layer) while the gold patch fixes the root cause (callee, producer, serialization layer), or cannot judge the scope. The agent found the right file in all 12. Front-loading patching in the first 10 steps correlates with lower success (ρ = −0.78); gathering context correlates positively (ρ = +0.68). | Observational; one run per task; Python and SWE-bench only; the 12 tasks are the hardest, and only three show an explicit caller/consumer/display gap in the paper's table; sample size for the ρ figures not stated |
| Gloaguen et al., [Evaluating AGENTS.md, arXiv:2602.11988](https://arxiv.org/abs/2602.11988) (v3) | Developer-written context files: +2.4% resolution on average, not significant (p = 0.21). LLM-generated files: −0.5% (SWE-bench) and −2% (their own CTXbench) and about 20% higher cost. Their recommendation: omit LLM-generated context files; write only what is not already in the repo. | Python only; one sample per agent and task; the paper gives 7% and 2.4% for the same comparison in different places and I could not reconcile them |
| Macke and Doyle, [Effect of Code Documentation on LLM Code Understanding, arXiv:2404.03114](https://arxiv.org/abs/2404.03114) | On 164 HumanEval functions with GPT-3.5 and GPT-4: a random wrong docstring is worse than none (22.1% and 68.1% success against 44.7% and 78.5% with no docstring); full comments gave no significant gain. | Two models, one benchmark, unit-test generation as the task; the authors warn of possible training-data contamination |
| Sabetto et al., [Impact of Comments on LLM Comprehension of Legacy Code, arXiv:2506.11007](https://arxiv.org/abs/2506.11007) | One IBM assembler module, four models, quizzes: extensive comments raised scores (96% and 90% against 84%); replacing 20% of comments with wrong ones had negligible effect; replacing all with an unrelated description cost about 12 points on a 10-question subset (73% to 61%). | A single module; the authors call the findings preliminary; the module may be in training data (a no-code run scored 75%) |

What this supports. Agents do patch symptoms, and gathering context before patching goes with success (point 1). Wrong comments hurt more than missing ones; accurate comments help modestly or not at all on small tasks (point 2). Prose context that restates the repo does not help and costs more (point 3). What it does not support: nothing here tests the specific rule "drop the comment that says why a proper fix was skipped", and nothing tests a 99.9% deletion; that is the presenter's practice, reported by the owner.

## What I measured here

- **Comments in `src/` and `tools/` (Python):** 13,758 `#` comments in 225,329 lines (6.1%); docstrings not counted. By area: `src/domains` 8.7%, `src/engine` 8.2%, `tools/` 5.5%.
- **Seeded sample of 39 comment blocks** (seed 20261116, of 7,139 blocks; the draw was 40 but only 39 printed; classified by me, one reader, so no inter-rater check): 17 restate what the code does; 8 are section banners or step numbers; 2 are noise (a self-path header; "unchanged" change narration); 8 carry a why, constraint or rule; 4 are pointers to code, a spec or an id (two also carry a why). So about 64% (25 of 39) are narration and about 31% (12 of 39) carry a why or a pointer, with a margin of roughly ±15 points on n = 39.
- **Pointers:** 302 comments cite a repo path; 9 of those paths are dead (3.0%). 686 comments cite a ticket id.
- **Markdown, who reads it:** unmeasured. The tool shards show 21 `Read` rows against 142 writes for rows whose path survived the 120-character cut (stored artifacts 2 against 24; staging 19 against 118). That is a floor, not a rate: paths are truncated, reads through Bash are not counted, and several weeks of shards are missing from this worktree. A citation count is not a read measure: 2,021 of 2,030 artifact directories are "cited", because each one's own closing ticket lists it (my control failed, so I discarded it). Scale: 7,935 stored-artifact files, 794k lines; search indexes only the first 500 characters of an investigation.

## The options

### 1. Quick fixes
- **A (recommended).** A new rule scoped to correctness and hard-rule fixes (not balance tuning, per lead-planner's caution): a workaround, or a "temporary" fix, must name the root cause and carry a ticket id in the same change; the explanation lives in the ticket, not in an apology comment. Enforce it with a report-only line in the close check that flags `TODO`, `HACK`, `workaround`, `temporary` or `for now` in added lines without a `TCK-` id, and have bug tickets state which layer holds the root cause (producer or consumer). This fits the study: the failures were wrong-layer fixes. Cost: false positives in the first weeks.
- B. Prose instruction only ("don't quick-fix"). Cheapest; the AGENTS.md study and the talk's own hierarchy say prose is the weakest lever.
- C. Ban the explanatory comment as the presenter does, with no ticket requirement. No evidence found; it hides the decision instead of recording it.

### 2. Comments
- **A (recommended).** Keep comments that carry a why, a constraint or a pointer; stop adding narration, banners, step numbers and self-path headers; run the citation resolver (already filed, report-only) over code comments as well as documents, since 3.0% of comment pointers are dead; and remove narration only on lines a ticket already touches, never as a sweep. `src/` is rpg's domain, so any removal there is rpg's call and is sequenced around M1's items. `tools/` is agent-working's.
- B. Leave as is. Dead pointers and narration keep accumulating at the current rate; wrong comments are the costly kind.
- C. A repo-wide comment deletion. The evidence does not show it helps (accurate comments help modestly); it would conflict with every open change in `src/`; and about one comment in three carries a why or a pointer that cannot be recovered from code.

### 3. Markdown
- **A (recommended).** Cut no process document yet. First add a read counter (a hook that counts `Read` of `stored_artifacts` and `staging_artifacts` paths with the full path, no 120-character cut) and run it 2 to 4 weeks. Then decide from the count. Keep without question: the Mechanics Bible, engine contracts, world-rules catalogue, parity ledger, decision records, and the one record a fresh session reads (#715 6889947724). Hold the rule "define information once": new prose may not restate code or another document, which the AGENTS.md study supports.
- B. For standard tickets, one ticket file with sections instead of three artifacts (`plan.md`, `investigation.md`, `test_plan.md`). A CLAUDE.md and `done_checker` change; the owner's direct yes. Their main reader, the pipeline, retires in Phase 4 (OD-5), so the consumer shrinks anyway, but I cannot yet show the hand path does not read them.
- C. Stop migrating staging artifacts to `stored_artifacts` at close. Smallest change, but it changes the close rule and the done-checker conditions.

## Not verified, so not relied on
- The talk itself and the owner's three relayed claims.
- PatchBench (a figure that guard-style patches inflate solve rates 1.83x) and the outdated-comments completion paper: not opened (the second returned a 403); the study "Talking to Itself While Coding" and the Frontiers pilot: not opened.
- Any figure from a search summary. Every figure in the table above comes from the paper text, with one exception: the early-patching correlation rests on a sample size the paper does not state.
- Generalisation: these are Python or benchmark studies on other codebases; none involves a 138k-line simulation with a rule catalogue.

## What I need from the owner
Pick an option per point, or ask for the read counter first. Anything touching CLAUDE.md, the ticket workflow or `done_checker` stays with the owner. I would file the report-only line (option 1A), the dead-pointer check on comments (option 2A) and the read counter (option 3A) as small agent-working tickets after the decision.
