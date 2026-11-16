---
content_type: doc
status: historical
layer: ai
authority: P2
audience: agent
tags: [ai, governance, delivery]
---

# OD-5 evidence pack: retire `implement-ticket.js`, `implement-epic.js` and the skill imitation

Evidence pack by agent-working-designer, 2026-11-16, for owner decision OD-5. Decided by the owner on #715 6911091662 (option A with both conditions; see the decision record). The pack is kept as the decision's evidence and is not updated after the decision. Owner condition (#715 6910853925): retiring is acceptable "but need a strong evidences from both our project observation and research/studies, recommendations from people". This pack gives that evidence and its limits. It does not decide. The "freeze now" recommendation in the first cut is withdrawn. Changes from v1: every external figure now comes from the source text, not a search summary; v1 had errors (Kim et al. is 260 configurations, not 180, and includes software-engineering benchmarks); the implementer's report is added.

## Conclusion first

1. **The strongest argument against retiring now is that the replacement is not built.** The pipeline runs three checks that the hand path does not. The implementer's report (below) names: (a) the test-scope floor (`test_scope_coverage_static`), so a hand Test phase can omit a required test directory with nothing catching it; (b) the capped-pytest enforcement and environment verdict from #935; (c) attested gate rows plus the backstop (tag check, plan questions, doc staleness) and independent Review and Architecture-Verify agent verdicts. The hand path uses `done_checker_static`, `docs_search`, the mechanism-registry advisory and the seat's own test runs, with no independent reviewer. A fourth, from the u24 testing lane: the pipeline's Architecture-Verify verdict has no hand-path equivalent on testing's closes; testing-planner accepts that only while its diffs touch no `src`, and would want it back for `src` durable state. That is the case for the OD-4 close check to cover an architecture verdict on `src`-touching PRs. The OD-4 close check is meant to replace these and is not built (Phase 2 is filed, not started). Retiring first would delete the only machine-run version before the replacement exists.
2. **Our own observation says the pipeline is not the working path.** 880 hand rows against 11 pipeline rows in W40-W45, no completed native run since W40, and no native run has ever completed end to end (#929). Non-use shows nobody chose it; it does not show the design is wrong, because the native path was broken for most of that time.
3. **The external evidence supports a single-seat hand path for sequential coding work but is not strong enough on its own to justify deletion.** It is mostly about what to build, and the one study that tests software-engineering tasks has small samples.

So the evidence supports "retire after the replacement exists", not "retire now". That is the plan's own order (removal after Phase 2). Decision options are at the end.

## Part 1: our own observation

Run rows (`agent-working/agent-monitoring/data/*/runs.jsonl`, rows with `workflow` = `implement-ticket` or `implement-epic`, split by `execution_mode`), worktree at origin/main f94417e6f:

| Week | hand | pipeline (native) | other |
|---|---|---|---|
| W38-W39 | no mode recorded (159 rows) | n/a | the field did not exist yet |
| W40 | 217 | 7 | 24 no mode; 1 probe row; 1 epic row |
| W41 | 274 | 4 | |
| W42-W45 | 151, 113, 98, 27 | 0 | |

Outcomes of the 11 pipeline rows: DONE 3 (all W40; 11, 11 and 15 agents; one took 21,182 s), NEEDS_HUMAN_INPUT 3, WORKFLOW_ERROR 3, NATIVE_GATE_SITES_UNPORTED 1, TAGS_NOT_REGISTERED 1.

**Native attempts since the port (gap 1).** agent-working-implementer (ubuntu) reports, in its own words: it ran the pipeline natively only for the native-port vehicle ticket TCK-20261115-SEARCH-STALE-FLAG-CHECKS-THE-INDEXED-CHECKOUT, three times on 2026-11-15, each time as a test of the pipeline on the owner's instruction (#715 6889470987, 6889489078), not for delivery:
- `wf_b59e5ed2-5d3`: TAGS_NOT_REGISTERED at Scope (a deliberate probe);
- `wf_d6a35058-f5d`: NEEDS_HUMAN_INPUT at the Plan gate;
- `wf_f48f4fae-569`: TESTS_FAILED at Test, after which the ticket was hand-finished (#715 6894904885).
TESTS_ENVIRONMENT_FAILED has not occurred in a real run; it exists only in a static source pin. The implementer's own tickets all go the hand path. These runs are the implementer's report, partly cross-checked by its run rows; they are not in my worktree's shards, so I did not count them myself. **Not yet answered: u24's seats.** The question goes through lead-planner to lead-planner-u24.

**Who launches it on purpose:** on ubuntu, nobody except as the owner-directed port test. u24: lead-planner-u24's reading of main's W45-W47 runs shards at db6b4579d (relayed by lead-planner, not read by me) shows no u24 native `implement-ticket.js` or `implement-epic.js` runs since 11-01; the only `pipeline_default` runs in that window are the three above; every u24 close was hand-orchestrated (owner_directed, batch_hand_close, small_change, investigation_only). Caveat: unpushed seat branches are not in main's shards. The u24 planners' answer on the pipeline-only checks is still to come.

**u24 testing lane (testing-planner, relayed by lead-planner and lead-planner-u24; not read by me):** no native runs since 11-01; every testing-lane run in W45-W47, including unpushed branch shards, is `execution_mode=hand` (15 tickets, owner_directed or small_change). Asked whether anything depends on a pipeline-only check, it answered no, and described what the hand path does instead: the test-scope floor is review (the planner names test files in each ticket's acceptance criteria and checks the implementer's counts plus CI, not a mechanical floor); capped pytest is `-n 1` with `free -m` and a host go by hand, not tool-enforced; independent Review is two seats as PR comments. It also said there is NO Architecture-Verify verdict on testing's hand closes, calls that a real difference, and accepts it only because its diffs are tools, tests and workflows with no `src`; it would want Architecture-Verify back if testing touched `src` durable state. 

**u24 rpg lane (rpg-planner and rpg-implementer, relayed by lead-planner and lead-planner-u24; not read by me):** no native `implement-ticket.js` or `implement-epic.js` since 11-01, pushed or not; every close was by hand with `record_hand_orchestrated_closure`. On pipeline-only checks the answer is mostly none, with one exception: the test-scope floor is a real gap on the hand path. They report that #931's first push followed a hand-scoped 147-test run with no `ci_lanes`, and CI caught 5 failing jobs; rpg now has a standing rule "ci_lanes or the CI-equivalent set before any push ask", enforced by hand. rpg-planner's view: if the pipeline retires, the floor is the one check worth keeping or porting to the hand path. Capped pytest is by hand; review is rpg-designer plus rpg-planner's PR comment. My check: PR #931 is open and its checks on 2026-11-16 show 5 failing jobs (Architecture / docs / static, Code health, Perf / cert / arena, Unit core / world, Unit infra / observability); the 147-test run and first-push timing are rpg's account, which I did not verify.

**u24 summary:** 0 native runs across all lanes since 11-01. Two gaps on the hand path: no Architecture-Verify stand-in (testing and agent-working; low risk while their diffs are not `src`), and the test-scope floor (rpg; one real miss).

**u24 agent-working lane (agent-working-planner-u24, relayed; not read by me):** read the W44-W46 shards in its worktree (an unpushed epic-close commit included) and the unpushed shards of the agent-working-u24 and agent-working-designer-u24 seats: every row is `execution_mode` hand (implementer-u24 22, planner-u24 3), 0 non-hand rows. Nothing depends on a pipeline-only check. Stand-ins: the test-scope floor is the implementer's scoped set checked by the planner against the changed files in PR review (#917, #919, #921); capped pytest is not enforced, relying on the no-full-suite rule and light runs; Review is a planner PR comment plus `record_review`, plus a designer review; Architecture-Verify has no stand-in (tools and docs work, seldom `src`). Its stated gaps: Architecture-Verify has no stand-in, and the scope floor is reviewer-checked, not tool-checked. So two u24 lanes (testing, agent-working) independently name Architecture-Verify as the one check with no hand stand-in.

Note the two reports differ in emphasis, not in fact: the ubuntu implementer lists what the pipeline does that the hand path does not do mechanically; testing-planner says the hand path covers the same ground by review and convention. Both agree the hand path replaces tool enforcement with seat practice.

**`implement-epic.js`:** one epic row in W40 (mode `workflow`, on a probe); the implementer has not used it since 10-01 and its shards show none. One-line conclusion: no evidence of use.

**Cost, as point samples only (the shards record agent count and duration, no tokens):**
- 10-04, `wf_ca51b3b4-356` for TCK-20260919-RAW-LEGACY-FACTION-ENUM-HOSTILITY-SWEEP: died with `ReferenceError: bash is not defined` after Scope; 6 agents, about 277k tokens, none reached Implement (source: that ticket, line 258). Lead-planner described this as an 11-14 crash; the dated source says 10-04.
- 10-09: 925,732 tokens, 20 agents, 27.8 min, died at the Test site (source: TCK-20260930-NATIVE-PORT-SMALL-TICKET-NATIVE-RUN; the plan's "about 925k" matches).
- The three 11-15 runs (same ticket's Test Summary; correction added 2026-11-16 before storing, after agent-working-planner pointed to the record; my earlier text said none was recorded and was wrong): `wf_b59e5ed2-5d3` 449,009 tokens, 8 agents, 80.8 s (TAGS_NOT_REGISTERED); `wf_d6a35058-f5d` 673,649 tokens, 11 agents, 224.6 s (NEEDS_HUMAN_INPUT); `wf_f48f4fae-569` 1,282,824 tokens, 21 agents, 2,907 s (TESTS_FAILED). About 2.4M tokens in total; none of the three completed.
Five samples, all from runs that did not finish (the 3 DONE runs of W40 have no token figure in the shards). They show what a failed run costs, not what a successful one costs. Whether to get a fuller cost figure is a question for the owner.

**Maintenance:** `.claude/workflows/implement-ticket.js` is 2,423 lines, all workflow files 5,509 lines (f94417e6f). The plan puts source-pinned tests at about 61 (not re-measured). #935 shows the pipeline still attracts work.

## Part 2: external research and practitioner write-ups (read from the sources)

Each row was read from the page or paper text by a fetch agent. Short quotes are from the sources; figures I could not read in the source text are marked.

| Source | What it says (from the source) | Bears on our question |
|---|---|---|
| [Kim et al., Towards a Science of Scaling Agent Systems, arXiv:2512.08296](https://arxiv.org/abs/2512.08296) | 260 configurations, 5 architectures, 6 benchmarks, including SWE-bench Verified and Terminal-Bench. On sequential planning every multi-agent variant degraded (PlanCraft, relative −39% to −70%); on decomposable financial reasoning centralized coordination gained +80.8%. On SWE-bench Verified all four multi-agent architectures were slightly below the single agent (single 0.522; Hybrid −2.1%, Centralized −3.1%, Decentralized −5.4%, Independent −14.9%). Terminal-Bench: Independent +1.7%, Centralized −19.2%. | The most direct study for coding work. Direction: multi-agent coordination did not help on SWE tasks. |
| same paper, limits (fetch-agent reading, PDF not checked; kept out of the conclusion) | The SWE-bench and Terminal-Bench results use 20-instance subsets; the paper says pairwise comparisons are "underpowered at n=20", and its bootstrap intervals are about ±20 points per cell. The "about 45% single-agent baseline" threshold rests on an interaction term whose cluster-robust p-value the paper's tables give as 0.105 (Holm 0.084), which the text calls "suggestive". The text says 8 models and 260 configurations, but its Table 16 has 9 models, an inconsistency I could not resolve. | So the SWE-bench result is a direction, not a firm number. Do not cite the 45% threshold as a rule. |
| [Xia et al., Agentless, arXiv:2407.01489](https://arxiv.org/abs/2407.01489) (v2) | Three-phase fixed pipeline (localize, repair, validate). SWE-bench Lite: 96 of 300 (32.00%), average cost $0.70, the highest among open-source approaches in its table; higher figures exist for closed-source tools. Authors' threats to validity (read from a summary, not the text): possible data leakage in SWE-bench Lite, results may not generalize beyond it. | Supports fixed, simple pipelines over free agents. Its pipeline is three single-model stages, not 11-15 coordinating agents. I did not read v1, so v1 figures (27.33%, $0.34) are not cited. |
| [Cemri et al., Why Do Multi-Agent LLM Systems Fail?, arXiv:2503.13657](https://arxiv.org/abs/2503.13657) (v3) | 14 failure modes in 3 categories (system design, inter-agent misalignment, task verification) from 1,642 annotated traces across 7 open-source frameworks; failure rates of 41% to 86.7% on 7 state-of-the-art systems; "performance gains ... are often minimal". | Coordination and specification failures are the common causes, and a many-agent pipeline multiplies those chances. The frameworks are not ours, and the paper does not test a repo workflow. |
| [Anthropic, How we built our multi-agent research system](https://www.anthropic.com/engineering/multi-agent-research-system) (13 Jun 2025) | Lead Opus 4 with Sonnet 4 subagents "outperformed single-agent Claude Opus 4 by 90.2% on our internal research eval"; agents use about 4x the tokens of chat and multi-agent systems about 15x. It says domains that "require all agents to share the same context or involve many dependencies between agents are not a good fit", and that "most coding tasks involve fewer truly parallelizable tasks than research". | Strongest pro-orchestration source, and it says itself it is for wide parallel research and not for coding. |
| [Anthropic, Building effective agents](https://www.anthropic.com/research/building-effective-agents) (19 Dec 2024) | Workflows are "orchestrated through predefined code paths"; agents direct their own process. "Find the simplest solution possible, and only increas[e] complexity when needed." A note says much of the tooling described "has changed since December 2024". | The advice favours the simplest pattern that works. The note limits how much weight the 2024 text carries. |
| [Cognition, Don't Build Multi-Agents](https://cognition.com/blog/dont-build-multi-agents) (Walden Yan, 2025-06-12) | Principles: share full agent traces; actions carry implicit decisions. Default: "a single-threaded linear agent". | Argues for the hand path's shape (one seat, one branch). A practitioner argument with no measurement. |

### What the external evidence does and does not support
- Supports: for one ticket's sequential edit-and-test work, adding coordinating agents does not help and often hurts (Kim et al. on SWE tasks, directionally; Anthropic's own caution on coding; Cognition). A single-seat hand path is the safer default.
- Does not support: deleting a tested, existing tool. These sources are about what to build. The pipeline's value is in the gates it runs (Conclusion 1), not in its use of many agents, and none of the sources tests that.
- Limits: the one SWE study has 20-instance subsets; four of the six sources are vendor or practitioner positions without data; I read Agentless v2 only, and its limitations from a summary.

## Decision options for the owner

- **A. Retire in Phase 4**, after the OD-4 close check has been in use (by owner practice) for 2 weeks and meets two conditions the lanes named: (1) a **mechanical test-scope floor**: the check reports, per PR, whether the tests that ran cover the directories the changed paths require (the one real miss is rpg's #931); (2) an **architecture verdict on `src`-touching PRs**, where Architecture-Verify has no hand stand-in. Capped-test enforcement and independent review stay by seat practice, which every lane reports as working. The owner may instead accept losing either condition. Tags exist, so retirement is recoverable.
- **B. Finish the native port** and keep it as a supported path. Nothing in Part 1 or Part 2 supports this for single-ticket work, and it is the only option that costs new work.
- **C. Leave as is**, no removal and no new work. Costs the maintenance figure above.
- **Separate:** `implement-epic.js` and the skill imitation; there is no evidence of use for either.

My lean: A, with its two conditions. They turn the missing replacement into Phase 2 acceptance items instead of a footnote: the gate job carries a mechanical test-scope floor, and an architecture verdict line for `src`-touching PRs.

## Open before this goes to the owner
1. Nothing on native use: all lanes on both hosts are answered (Part 1). The u24 answers are relayed readings, not mine, and rpg's #931 detail is unverified beyond the current failing-check count.
2. Kim et al.: three small text gaps (about 42 characters each) were not read, and the threshold, p-value and per-model readings are the fetch agent's reading of the tables, PDF not checked. The conclusion does not rest on them (lead-planner, 2026-11-16: no PDF check needed).
3. Agentless v1 and the Anthropic "Managed Agents" post that the 2024 note points to were not read.
4. Whether the owner wants a fuller cost figure.
