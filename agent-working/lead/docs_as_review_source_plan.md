# Plan: documents as the review source, kept correct

Status: APPROVED rev 3.2, 2026-11-08 (#715 comment 6720445592). The owner said: "approve full plan staged, J pilot only, yes to all three". That means: batches A-I are approved for staged implementation; batch J is approved for the read-only pilot (J1-J2) only, and J3's scope will be decided from the J2 report; the CLAUDE.md policy lines are approved in principle, and the owner reviews the actual diff before merge; Q5 is the weekly scripted check at the existing weekly close plus 2-3 retro spot checks. Batch I still waits on the owner's dispositions of `review_followups_2026-11-07_all.md`. History: rev 1 drafted the plan (2026-11-07); rev 2 answered `docs_as_review_source_plan_review.md` (X1-X29); rev 3 answered `_review_v2.md` (R1-R5); rev 3.1 added batch J; rev 3.2 answered `_review_v3.md` (V1-V6). Dispatch is the owner's; lead-planner sends each batch to its owning planner as a finding.

## Goal (owner, 2026-11-07)

> "we should document every helpful detail, review using documents only not just help reduce the effort but reduce the complexity from reading, since sometime we don't care about every single detail from implementation, but yes, the document should not stale and must be correct"

A reviewer, human or agent, should be able to answer feature, design, architecture and behaviour questions from documents, and know how far to trust each answer. Code is read when a document's evidence is missing, invalidated or insufficient, when a doc doesn't answer the question, or when a spot check selects it (P5).

## Why now: evidence (origin/main 531010a9a, re-checked at 297494469 on 2026-11-08)

- About 1.1M agent tokens were spent re-reading the same areas three or four times: the outside review, my findings check, the CV check, the fact bank, and the inventory. This figure comes from session usage. Monitoring records no tokens: `runs.jsonl` has duration only, and events carry a unitless `cost_proxy_score`.
- Eight documents were reported wrong or incomplete; one (substrate) was withdrawn on 2026-11-08. All except the README are still wrong at 297494469:
  - `docs/engine/deterministic_execution.md:69,182` says Canonical is unimplemented, while `:71` shows it is implemented.
  - `docs/architecture/observability_hot_path_safety_contract.md:124` says an exhausted message is "routed to the DLQ stream and ACKed off the source stream". It doesn't say what happens when the DLQ write fails, and the code ACKs anyway (`src/observability/stream/consumer.py:157-164`). This is a defect plus a contract gap, not a doc to rewrite to match the code: the contract gains an explicit failure row once the intended behaviour is decided (R3).
  - `src/engine/scenario_checkpoint.py:86-88`, a code comment, says the base seed is "irrelevant post-restore". That describes the restore-seed defect as if it were intended, so it is fixed together with that defect's ticket.
  - `README.md` named a `WorldLoop` class and `*Aspect` entities that don't exist, and listed Promtail. This was fixed in #843 (bb70d0cb5).
  - `CLAUDE.md` lists 6 Bible chapters; there are 7 (`07_social_political_dynamics.md`).
  - ~~`docs/engine/contracts/substrate_baseline_contract.md:27` says the kernel has 6 phases; it has 7.~~ Withdrawn 2026-11-08: `:40` of the same file already reconciles it (6 authoritative phases plus the PERSISTENCE hook make kernel.md's 7). Found by rpg-planner-ubuntu and confirmed by lead-planner at 297494469.
  - `docs/engine/known_limitations.md` doesn't record the defects found on 2026-11-07: DLQ ACK, restore seed, watchdog reset, dirty tag, harvest double count, shutdown success.
- The worst findings came only from code, because each doc stated the intent and the code did something else. A docs-only review would have repeated those claims, which is why P5 keeps risk-triggered code inspection.
- Counts re-derived by hand disagreed with each other. The baselined layer edges came out as 129, 145, 156 and 157; src lines came out as 132k and 134k, the first from a stale checkout.

## What already exists (reuse it; don't rebuild)

| Mechanism | What it does | Gap |
|---|---|---|
| D25 audit, `docs/audits/D25_engine_docs_drift.md` (TCK-20260817-AUDIT-ENGINE-DOCS-DRIFT) | Canonical-doc-per-topic map, plus the "satellites cross-link, never restate" rule | Covers only 4-5 topics; its follow-up (contracts/ and matrices/ at full depth) was recommended but never filed |
| `tests/docs/test_doc_path_existence.py` | Every cited path exists | Catches renames, not wrong claims |
| `tests/docs/test_doc_integrity.py` + `docs/engine/manifest.json`, `test_kernel_phase_names_consistent.py` | Fact-parity tests for enums and phase names | Only a handful of facts |
| `docs/parity_ledger/` (total unsettled: two parses gave 6,201 and 2,300; P2 settles it) | Bible-to-code parity, with `v2_evidence` and `test_path` | Mechanics only; 200 of 1,687 P0 entries have a test_path |
| `registries/mechanisms.yaml` + `tools/mechanism_registry/mechanism_registry_changed_code_check.py` (255 lines) | Flags a mechanism whose `implemented_by` code changed while its entry didn't | The pattern P1 reuses for docs |
| `docs/REGISTRY.yaml` + `tools/generate_registry.py --check` | Generated doc index, with a drift check | Index only, not claim correctness |
| `docs/performance/phase_inventory.md` (generated, `--check`) | A count that is generated, not handwritten (PERF-D6) | The pattern P2 reuses for scale numbers |
| `known_limitations.md`, `intentional_divergences.md`, ADRs | Limits, divergences and decisions | Limits aren't updated when a defect is found |
| Document-Update phase (`implement-ticket.js:1211-1273` at 667199567), `doc-updater` (90 lines), `doc_staleness_check.py` (144 lines), Verify's `check_docs_to_update_coverage` | Updates and gates the docs Investigate listed | Nothing searches for other docs that restate the changed fact (below) |

## Normative sources and precedence (R3)

The plan keeps the existing normative sources and adds no `docs/specs/` folder or spec format. When two sources disagree, the higher one wins:

1. The world-rules catalog (`docs/world_rules/`), with accepted Rule IDs.
2. The Mechanics Bible (`docs/mechanics/`).
3. The engine contracts (`docs/engine/`, `docs/engine/contracts/`) and the architecture contracts (`docs/architecture/*_contract.md`).
4. The parity ledger (`docs/parity_ledger/`) and `intentional_divergences.md`. These record whether the code matches 1-3; they don't define intent.

Everything else (guides, READMEs, design philosophy, runbooks) is explanatory. It describes the normative sources and the code, and links to them instead of restating them. History docs (`docs/archive/`, `docs/audits/`, plans whose frontmatter `status` is `historical` or `superseded` (an active plan is a living doc), reviews, test reports, run records, ADR context) are records and are never rewritten.

The rule that follows: when code and a normative doc disagree, that's a defect or a proposed divergence. Nobody edits the normative doc to match the code. The difference goes to the rule owner (rpg-designer through the world-rules catalog) as a defect ticket, or as an `intentional_divergences.md` entry if the owner accepts the code's behaviour.

## Owner correction (2026-11-07): extend the existing doc phase and agent first

#837 went through the standard pipeline and still left its satellite docs stale. doc-updater's input is only Investigate's `## Docs Requiring Update` list ("never something you derive yourself", `doc-updater.md` Step 0). The gate checks only that some `docs/` path changed. Nothing searches for other docs that restate the changed fact, which is the pattern behind all six recent-work misses.

A replay at 531010a9a shows that a path-citation search works but is noisy. Searching `docs/` for #837's changed src files (`executor.py`, `worker_protocol`, `worker_manager`), with `docs/archive`, `docs/audits` and `REGISTRY.yaml` excluded, finds all three stale satellites (`simulation_kernel_contract.md`, `deterministic_execution.md`, `kernel_concurrency_design_philosophy.md`) among about 19-25 candidate docs per path. An old-behaviour term (`readonly_view`) finds two of the three in 6 docs, 4 of them history. So the search needs the history exclusion and a triage step, which is why F2 makes the call and F3 only reports.

| # | Change | Where | Owner |
|---|---|---|---|
| F1 | Investigate builds `## Docs Requiring Update` by search, not only by judgment. Inputs: the changed src paths, their importers (graphify's import graph) and the `mechanisms.yaml` entries whose `implemented_by` they're in, the changed public symbols, the old-behaviour terms the ticket removes, and the topic's canonical doc from the topic map (P4). The output has three lists: **required** (normative or canonical docs that state the changed fact), **candidate** (other hits to triage, direct hits first, then importer and mechanism hits), and **excluded** (history docs, with the reason). | the investigator prompt in `implement-ticket.js`; `.claude/agents/investigator.md` | agent-working |
| F2 | doc-updater gets a satellite step after the required docs. For each candidate, it updates the doc if it restates the changed fact, or reports it as `docs_skipped` with a reason. It edits explanatory docs only. A normative doc is changed only when the ticket itself changes the intended behaviour and cites the rule owner's approval; otherwise a disagreement is reported as a defect or a divergence (see "Normative sources"). History docs are never edited. This lifts "never derive yourself" for candidates only. | `.claude/agents/doc-updater.md` Step 0 and "What to Do" | agent-working |
| F3 | The doc-staleness gate adds an advisory list of docs that cite a changed src file or symbol but weren't touched, minus the history exclusion. It never blocks (the owner's proportionate rule). Hits on docs for a critical invariant (P5) are listed first and named in the close summary. | `tools/gate_checks/doc_staleness_check.py` | agent-working |
| F4 | Hand-orchestrated closes get the same step: CLAUDE.md's "After Work" list gains "run doc-updater, or the F1 search, before close". Today a hand close has no doc phase at all. | CLAUDE.md "After Work" (governing file, needs the owner's direct OK); `docs/guides/delivery_process.md` | agent-working + owner |
| F5 | F1's search also covers comments and docstrings in the changed src files, but only ones that state an invariant, lifecycle, concurrency or recovery behaviour (the restore-seed comment). Other comments are out of scope. | `investigator.md`, `doc-updater.md` | agent-working |

P1's drift report is the backstop between tickets: it catches docs that go stale when no ticket touched them. It reuses F3's matching, run over each doc's baseline-to-HEAD range instead of one ticket's diff.

## Proposal: five parts

### P1. Every behaviour doc carries its evidence and a verification baseline (doc-level)

Fields (optional frontmatter on contracts, Bible chapters, architecture docs, runbooks and the README):
- `evidence_paths:` lists the code and test files the doc describes. List files, not directories.
- `verified_by:` names the ticket or PR that verified the doc. That ticket says what was read and any exclusions.
- `verified_at:` is the commit SHA of the code that was read.

What verified means (R2):
- A doc gets `verified_by` and `verified_at` only when someone checked every behaviour claim in it against its evidence at that revision. Fixing one line, or reading the code for some other purpose, doesn't verify the doc.
- If the evidence is insufficient (a claim has no test and the code can't settle it), the fields stay unset and the doc stays unverified. The ticket records which claim blocked it.
- A doc without `verified_by` is unverified, and every report shows it that way. No state is stored besides these fields; "needs re-verify" is derived on each run (X2).

Drift report (reuses the mechanism-registry pattern):
- The baseline is the commit that last changed the doc's `verified_by` line, found from git history. That makes the baseline survive a squash merge and include the verifying PR's own edits.
- The report lists a doc as "needs re-verify" when any of these is true:
  - an evidence path changed after the baseline, listing the changed files;
  - an evidence path was deleted or renamed;
  - the doc's own text changed after the baseline, since that edit wasn't verified.
- It runs at ticket close (pipeline Finalize and hand closes) and weekly (see Q5). It's advisory and never blocks.
- To re-verify, read the changed files and the changed doc text, correct the doc, then set new `verified_by` and `verified_at` values. A doc with no drift keeps its baseline, but that only means it hasn't changed, not that it's correct. Spot checks (P5) still apply.

Pure design and history docs need none of these fields; they are true as records.

### P2. Numbers are generated, never handwritten

- One stats tool, `tools/project_stats.py --ref <sha>`, prints:
  - src lines and modules;
  - test files and static test functions;
  - tickets, and merged PRs (dated, since that count changes over time);
  - roles, subagents, hooks and skills;
  - parity-ledger entries by status and priority, and import contracts and baseline edges;
  - metric families and alert rules.
- It writes the generated page `docs/architecture/project_facts.md`, with a `--check` like the phase inventory and REGISTRY have.
- The page header gives the ref SHA, and each count states its counting rule (what is counted, which paths, which parser). That settles the parity-ledger total.
- Docs, CV rows and reviews cite this page instead of re-deriving a number.

### P3. Known defects and limits are documented when found, with a lifecycle

- When an audit or a ticket finds a behaviour defect, the same change adds a line to the subsystem's limits section, or to `known_limitations.md`, citing the defect ticket.
- When the fix lands, the fix PR moves the line into the ticket's completion summary. The limits section keeps a one-line "fixed in <ticket>" pointer only if the limit was published, for example in a release note.
- The six defects from 2026-11-07 are the first entries.
- The Definition of Done gains this wording next to "Docs were updated if behavior changed".

### P4. One topic map with canonical sources, extended from D25

- `docs/architecture/doc_topic_map.md` (lead) has one row per fact group: kernel phases, pipeline order, determinism and RNG, checkpoint and restore, API and read models, WebSocket, observability stream and DLQ, alerts, watchdog, content pipeline, economy and conservation, factions, the agent workflow, and so on.
- Columns:
  - the canonical doc;
  - its normative source, with precedence from "Normative sources" above;
  - its verification status, derived from the P1 fields by the drift report, never typed by hand;
  - satellites, which link to the canonical doc instead of restating it.
- A topic may be one contract; the map names a canonical source per fact group, not one file per subsystem (X17).
- D25's never-filed follow-up (contracts/ and matrices/ at full depth) is filed as part of the seed work.

### P5. Review rules

These go in `docs/guides/delivery_process.md`, plus one CLAUDE.md line (X27 wording, owner's direct OK):

- **Start from documents.** A review starts from the topic map and the canonical docs, and uses the P1 status and the drift report to judge how far to trust them.
- **When code is read.** A review reads code when:
  - the claim's evidence is missing (no `verified_by`);
  - the evidence is invalidated (the drift report flags the doc);
  - the evidence is insufficient (no test exercises the claim, a test covers only a narrow case such as the restore test at seed 0, or, for a critical invariant, the only test was written in the same change as the code (X18));
  - no doc answers the question;
  - the claim is picked for an independent spot check.
- **Critical invariants need evidence, not a re-read every time (R4).** Critical invariants (determinism, conservation, persistence and restore, concurrency, message acknowledgement) need adequate implementation-level evidence: a verified doc plus an independent test of the claim. A weekly audit doesn't re-read their code unless one of the triggers above applies.
- **Scope.** A review report says whether it was a docs-and-governance audit or an implementation audit. A docs-only audit never claims the code is correct.
- **Pin (R5).** Every audit names the commit it read and reads files at that commit: `git show <sha>:path`, or a worktree at the pin. A branch behind origin/main is a valid subject when the review is about that branch. The rule bans only an unpinned read of a stale working tree, presented as if it described current main. The session-start behind-origin warning stays, since it caught exactly this error.
- **Fix in the same PR.** A wrong explanatory doc found during review is fixed in the PR that found it. A wrong normative doc goes to its rule owner.

## Recent-work doc audit (PRs merged 2026-11-01 to 2026-11-07, plus #786)

A read-only agent checked every merged PR at 531010a9a; lead-planner re-read items 1, 2, 4 and 5 itself. 9 PRs kept their docs correct. 6 left a doc missing, wrong or stale elsewhere: the PR updated the doc it was told about but missed other docs that restate the same fact.

The "Class" column (R5) separates **confirmed** misses, which F1-F3 must find from the PR's own diff, from the rest. **Not diff-findable** means no search over that PR's diff can find it. **Judgment** means a fix is optional or a matter of interpretation. **History** means the doc must not be edited, which makes it a negative test: F2 must leave it alone.

| # | Doc fix | From | Class | Owner |
|---|---|---|---|---|
| 1 | `docs/engine/contracts/simulation_kernel_contract.md:65-73` still says the packet seed is "dead"; since #837 the packet carries the world seed (`executor.py:301`). | #837 | confirmed (path citation hit, replayed) | rpg |
| 2 | `docs/engine/deterministic_execution.md:149` says workers get `readonly_view()`; concurrent workers get a `WorkerPacket`. | #837 | confirmed (path and term hit, replayed) | rpg |
| 3 | `known_limitations.md:88` and `deterministic_execution.md:36,179`: cross-reference divergence 2.147 and the long equivalence test. | #837 | judgment | rpg |
| 4 | `docs/observability/hard_law_monitor.md:16,49` says "eight laws"; the code has 9 (`LAW-POSITION-IN-WORLD`, added 2026-10-10). | #823 (inherited) | not diff-findable; for the P1 drift report | rpg |
| 5 | `README.md:141` listed Promtail; compose has Alloy. Fixed in #843. | #786 | confirmed (term hit; 8 non-history hits, replayed) | lead |
| 6 | `docs/architecture/kernel_concurrency_design_philosophy.md:71,130` diagrams still show a per-packet seed. | #837 | confirmed (path and term hit, replayed) | lead |
| 7a | No doc for the pinned-record quiet gate (`tools/perf/quiet_gate.py`). | #806 | not diff-findable (missing doc) | perf |
| 7b | `perf_baseline_policy.md:15,44` still says "schema 1.0" (it's 1.5). | #806 | candidate; confirm by replay | perf |
| 8 | `session_roles/functions/designer.md:19`, `planner.md:17` read as allowing ticket-only PRs, against #840. | #840 | judgment | agent-working |
| 9 | `import_linter_soak_review.md:179` says the phase19 contract is unenforced; it landed in #817. | #819 | history (negative test) | none |

Unverified: #807's retro wording, #822 against delivery_process, and whether #826's and #823's disclosure lines went stale later.

## Acceptance criteria

1. **Regression replay:** F1-F3, run on the diffs of #837 and #786, put items 1, 2, 5 and 6 in their required or candidate lists. Item 7b is added if its replay confirms it. Item 9 lands in the excluded list, and F2 doesn't edit it.
2. **No false verification:** a doc without `verified_by` shows as unverified in the drift report and the topic map. No seed doc gets the fields without a ticket that records the claims checked.
3. **Drift signals:** a changed, deleted or renamed evidence path, or a doc-text edit after the baseline, each produce "needs re-verify" in a test fixture.
4. **No defect written into a normative doc:** doc-updater's instructions say this, and the seed batch's DLQ and restore-seed items follow it.
5. **Report scope:** every audit report states its pin and whether it is a docs or an implementation audit.
6. **Facts page:** `project_stats.py --check` fails when the page is stale, and the header carries the ref and the counting rules.

## Seed work and effort estimate

Measured basis: DONE implement-ticket runs in W43-W45 on origin/main (221 runs) took a median of 9 minutes for a hotfix (p75 21) and 19 minutes for a standard ticket (p75 46). That is the pipeline's wall time only. Review, CI and your merge add calendar time, usually 0.5-1 day per PR with the merge waits. Monitoring records no tokens, so the token figures below are my estimate from comparable sessions, not a measurement.

| Batch | Tickets (tier) | Owner (PRs) | Depends on | Seat time | Tokens (estimate) |
|---|---|---|---|---|---|
| A. Doc fixes and limits lines: items 1, 2, 4 and 6, the still-wrong docs above (`deterministic_execution`, CLAUDE.md; `substrate_baseline_contract` withdrawn), the DLQ contract failure row, and the six P3 limits lines | about 5 hotfix: rpg 2, lead 1, perf 1, agent-working 1 (CLAUDE.md, needs your direct OK) | rpg, lead, perf, agent-working (4 PRs; perf's and agent-working's can ride with other work) | none. The DLQ row waits on the intended behaviour from the DLQ defect ticket. The restore-seed comment rides with that defect fix. | about 1-2 h per domain | 0.3-0.6M |
| B. Pipeline changes F1, F2, F5 (prompts) and F3 (gate advisory), with the replay fixtures | 2 standard | agent-working (1 PR) | none | about 1 day | 0.8-1.5M |
| C. The P1 fields, drift report and baseline derivation, plus the frontmatter schema and validator; the weekly hook (Q5) | 1 standard | agent-working (same PR as B or the next) | none | about 1 day | 0.6-1.0M |
| D. The P2 stats tool, facts page and `--check` | 1 standard | agent-working (1 PR) | none | about 0.5-1 day | 0.4-0.8M |
| E1. F4 (hand-close doc step), P3 Definition of Done wording, the P5 rules that don't depend on P1 (scope, pin, fix in the same PR, normative docs go to the rule owner), CLAUDE.md lines | 1 hotfix | agent-working + your direct OK on the diff (rides with B) | B | about 1 h | 0.1-0.2M |
| E2. The P5 rules that cite P1 (the "when code is read" triggers on `verified_by` and drift, critical-invariant evidence) | rides in C's ticket | agent-working | C | included in C | included in C |
| F. Topic map (P4) | 1 standard | lead (1 PR) | A; uses C's status if present | about 0.5-1 day | 0.4-0.8M |
| G. D25 follow-up: contracts/ and matrices/ at full depth | 1 standard (audit) | rpg | F | about 1 day | 0.6-1.2M |
| H. Seed verification of about 8 canonical docs (kernel, determinism, checkpoint, API and read models, observability stream, watchdog, content pipeline, README) under P1's rule, claim by claim | 2-3 standard, split by domain | rpg mostly, lead (README, architecture) | A and C | about 2-3 days | 0.8-1.6M (about 0.1-0.2M per doc) |
| I. Fold the 126-row review dispositions into docs | 1-3 hotfix | per domain | your dispositions on `review_followups_2026-11-07_all.md` | unknown until the dispositions are in | 0.3-0.8M |
| J1-J2. Stale-doc detection pilot and evaluation (rev 3.2): see below | 1 standard | agent-working | B (reuses F1/F3 matching) | about 0.5-1 day | 0.3-0.6M |
| J3. Stale-doc fixes by domain | sized from J2's results; placeholder 5-9 hotfix | rpg, lead, perf, agent-working, codebase | J2 and your go on its scope | placeholder 1-2 weeks | placeholder 1.7-3.4M |

**Total:** about 21-28 tickets in about 10-13 PRs across rpg, lead, perf, codebase and agent-working, with two governing-file edits that need your direct OK. Tokens: about 6.3-12.5M (estimate). Calendar: about 3 weeks if A, B-E, F and J run in parallel lanes, gated mostly by merges and by H's reading. The critical path is A → C → H. B, C, D and E1 can start at once; E2 rides with C; F and G follow A; J1-J2 follow B; J3 follows J2. J3's figures are placeholders until J2 reports.

### Batch J: old and stale docs (rev 3.1, staged in rev 3.2)

Why it's needed: at origin/main 297494469, `docs/` has 1,212 `.md` files. `archive/` (448), `brainstorm/` (34) and `audits/` (31) are history. The 251 `plans/` files are a mix of finished and active plans. About 450 others are living docs (`engine/` 93, `world_rules/` 78, `simulation/`, `ai/`, `architecture/`, `guides/`, `runbooks/` and the rest). Batches A and H touch only about 18 of them. The drift report sees only docs that carry P1 fields, so a stale doc without them stays invisible unless a ticket or a review happens to hit it.

**What the signals mean.** Every J signal marks a doc as *possibly stale*, never as wrong. Only a triage read or a P1 verification can confirm a doc is wrong. The signals are:
- **evidence newer:** a cited src or test path changed after the doc's last edit. Ranked by the lag and by how many cited paths changed.
- **unresolved name:** the doc names a path or symbol that the pinned tree doesn't resolve. It is reported as *unresolved*, not *deleted*, because it may be renamed, external, generated or just a prose word. A known rename (git's rename detection) is shown with its new name.
- **plan lifecycle:** a `plans/` file whose frontmatter `status` isn't `historical` or `superseded`, but whose cited tickets are all in `done/`. Plans aren't excluded wholesale. A plan counts as history only when its frontmatter says so; otherwise it's a living doc and gets the other two signals too.

**Known limits of the signals, measured.** A replay at 531010a9a against the four known stale docs found:

| Doc | Result | Why |
|---|---|---|
| `simulation_kernel_contract.md` | flagged | 14 of its 21 cited paths are newer than the doc |
| `kernel_concurrency_design_philosophy.md` | flagged | 9 of 17 newer |
| `deterministic_execution.md` | missed | #837 edited one line of it, so the doc looks fresh while other lines stayed stale |
| `hard_law_monitor.md` | missed | it cites no src paths at all |

These are design limits of a timestamp signal. They're stated here rather than worked around: a partly updated doc is F1/F2's job at ticket time, and a doc that cites no code is caught only by P1 evidence fields or a review.

**Repeated triage (V5).** A doc triaged as *accurate* gets `reviewed_by: <ticket>` in its frontmatter. The detection run uses the same git-derived baseline as P1 (the commit that set the field) and stays quiet about that doc until its evidence or its own text changes again. `reviewed_by` means "triaged, no staleness found". It is weaker than `verified_by`, never shown as verified, and doesn't count toward the topic map.

**Stages:**
- **J1. Detection pilot.** Build the detection as a mode of the drift-report tool (C's tool if it exists, otherwise a standalone script that C later absorbs). Run it read-only at a pinned SHA. The output is a ranked list per owning domain.
- **J2. Evaluation.** Report:
  - how many docs are flagged, by signal and by domain;
  - the false-positive rate on a sample of about 20 docs read by hand;
  - recall against the labelled known-stale set: items 1, 2, 4 and 6 at 531010a9a, with items 2 and 4 labelled as undetectable by design;
  - a sized J3 proposal.

  You decide J3's scope from that report.
- **J3. Remediation.** Each owning domain triages its flagged docs:
  - **fix** the doc;
  - **retire** it by moving it to `docs/archive/` or setting `status: historical`, never by deleting it;
  - mark it **accurate** with `reviewed_by`.

  Topic-map satellites and runbooks come first.
- **Not in J:** verifying all ~186 normative docs (`engine/`, `world_rules/`, `mechanics/`) claim by claim, which would cost about 20-35M tokens. The topic-map docs are verified in H. The rest are verified when a ticket or a review touches them (P5).

J's acceptance criteria:
- J1 and J2: the run is pinned and read-only. The J2 report gives the counts, the measured false-positive rate and recall on the labelled set. Recall is reported as measured, never a pass threshold: no test or tuning targets the known docs (V1).
- J3: every flagged doc in the approved scope has a disposition. No history doc is edited and no doc is deleted. An *accurate* doc isn't flagged again while its evidence and text are unchanged.

Living-doc verification states (unverified, `reviewed_by`, `verified_by`, needs re-verify) are listed in the drift report. The topic map shows only its own canonical docs' status (V6).

**Where it pays back:** H is the expensive part. It is the same kind of reading that cost about 1.1M tokens on 2026-11-07, done once and recorded, instead of repeated per review. If later reviews start from verified docs, the batch repays itself after roughly 4-8 audits of the size of 2026-11-07's. That is a projection, not a measurement; X25's missed-findings check after the first two audits is the real test.

**Cheapest useful subset if you want to stage it:** A, B and E1 (about 8 tickets, 1.2-2.3M tokens, about 1 week). E1 needs only B, so the subset holds together without C (rev 3.2 fixed rev 3's E, which depended on C). That closes the satellite-miss loop on every new ticket. C, D, F, G and H can follow once A, B and E show fewer misses.

## Options considered

| Option | Verdict | Reason |
|---|---|---|
| Docs only, no evidence anchors, trust authors to update | REJECT | Seven wrong docs on 2026-11-07; trust without a drift signal decays. |
| Claim-level anchors (every sentence tagged with code lines and SHA) | REJECT for now | High authoring cost, and line numbers churn. Doc-level fields get most of the value; revisit only if doc-level proves too coarse. |
| A separate fact-registry YAML outside docs | REJECT | It would duplicate the docs and break the define-once rule. |
| A new `docs/specs/` layer or spec format | REJECT | It duplicates the world-rules catalog, the Bible and the ledger (X7, R3). The authority order goes in the topic map instead. |
| Blocking CI gate on doc drift | REJECT | The owner's rule: agent tooling checks are proportionate and advisory. The path-existence test already blocks dead paths. |
| Executable specs (assert every documented claim in tests) | DEFER | Already done where cheap. Extend only for facts that drifted twice (D25's recurrence rule). |
| Generated API docs from code (OpenAPI) | DEFER | Worth it when the API changes often; today it doesn't. |
| LLM-written docs regenerated from code on every change | REJECT | It reproduces the code's bugs and hides divergence. |
| Keep the outside review folder as a reference | REJECT as a source | It was written on a stale tree in gitignored `tmp/`; fold its verified content into repo docs (batch I). |
| A new standalone doc-checking agent or phase | REJECT | Widen the existing phase, agent and gate (F1-F5) instead. |
| Make F3 blocking | REJECT for now | The replay shows about 20 candidate hits per changed path; advisory first, promote only with low false-positive evidence. |
| Do nothing; audit from code each time | REJECT | That's 2026-11-07's cost (about 1.1M tokens) and its errors. |

## Risks

- **Risk 1:** a baseline is bumped without a real re-check (gaming). A bump needs `verified_by` naming a ticket that lists what was read. Retro spot checks re-read a sample.
- **Risk 2:** `evidence_paths` too broad, so docs are always flagged. List files, not directories.
- **Risk 3:** docs grow too detailed. "Every helpful detail" means behaviour, limits, decisions and numbers, not a line-by-line restatement of the code.
- **Risk 4:** the F1 search is noisy (about 20 candidates per path in the replay), so doc-updater spends tokens triaging. The history exclusion and the required/candidate split bound it. If triage cost shows up in the first runs, narrow candidates to direct hits only.

## Owner questions

1. Approve F1-F5, P1-P5 and staged implementation of batches A-J, or change any option's verdict? Or approve the cheapest subset (A, B, E1) first? For batch J, the reviewer and I recommend approving only the read-only pilot (J1-J2) now, and deciding J3's scope from J2's report.
2. The topic map and facts page live in `docs/architecture/` (accepted in X26). Confirm.
3. The CLAUDE.md lines (F4, P5 with X27's wording, and the 7-chapter fix) are governing-file edits. Approve the policy in principle now; you review the actual diff before it merges.
4. After approval, lead-planner sends each batch to its owning planner as a finding, with this plan as the shared reference. You dispatch.
5. **Weekly audit or retro spot checks only?** Recommendation, agreeing with the reviewer: both, kept light. Weekly, the drift report, the `project_stats.py --check` and the list of unverified canonical docs run as a script, with no agent re-reading code, at the existing weekly close (`make agent-monitoring-close-week`), so no new cadence is added. At each retro, a deeper independent spot check re-reads 2-3 verified docs against code, critical invariants first.

## Rev 3.2: response to the third review (2026-11-08)

Source: the third external review (`docs_as_review_source_plan_review_v3.md`; external AI reviewer, plan text only). Verdict: approve the direction, with minor corrections before full implementation; no redesign. The review file was removed once its points were dispositioned; its text is in git at d1fa1263c.

| # | Point | Disposition | Where it now lives |
|---|---|---|---|
| V1 | J's criteria must not require impossible detections or hardcode known findings | ACCEPT, and measured. The timestamp replay at 531010a9a flags only 2 of the 4 known stale docs (items 1 and 6), so rev 3.1's criterion "the ranking run lists items 1, 2, 4 and 6" was impossible. | Batch J "Known limits"; recall is reported, not a pass threshold. |
| V2 | E depends on B and C, but the subset was A, B, E | ACCEPT. E is split: E1 (needs B only) and E2 (rides with C). | Effort table; subset A, B, E1. |
| V3 | Signals mean "possibly stale", not "wrong"; classify unresolved symbols | ACCEPT | Batch J "What the signals mean". |
| V4 | Don't exclude all `plans/` before checking their status | ACCEPT. Rev 3.1 counted all 251 as history, and "Normative sources" listed "dated plans" as history. | Batch J plan-lifecycle signal. A plan is history only when its frontmatter says so. |
| V5 | Keep *accurate* dispositions so false positives aren't re-triaged | ACCEPT. A new optional frontmatter field, `reviewed_by`, uses P1's git-derived baseline. It's weaker than `verified_by` and never counted as verified. | Batch J "Repeated triage". |
| V6 | The topic map tracks canonical sources only; living-doc states go in the drift report | ACCEPT. Rev 3.1 said every unverified living doc shows in the topic map. | Batch J last paragraph; P4 unchanged (canonical docs only). |
| J1-J3 | Pilot, evaluate, then remediate from the results | ACCEPT | Batch J stages and effort table; J3's numbers are placeholders. |
| Owner | Staged approval, CLAUDE.md approved in principle with diff review, weekly scripted check plus retro spot checks | ACCEPT as recommendations | Owner questions 1, 3 and 5. |

## Rev 3: response to the follow-up review (2026-11-08)

Source: the second external review (`docs_as_review_source_plan_review_v2.md`; external AI reviewer, plan text only, not the repo). Verdict: conditional approval, no redesign. The review file was removed once its points were dispositioned; its text is in git at d1fa1263c.

| # | Point | Disposition | Where it now lives |
|---|---|---|---|
| R1 | ACCEPT and PARTIAL decisions were only in the disposition table | ACCEPT. Rev 2's note that "the plan text above is already edited" was wrong for X3, X7, X8, X9, X11, X13, X14, X15, X17, X18 and X21. | F1-F5, P1-P5, "Normative sources", "Acceptance criteria". |
| R2 | Don't assign `verified_at` to a doc that wasn't verified; add `verified_by`; detect doc edits; keep unverified when evidence is insufficient | ACCEPT. Rev 2's seed item 2 stamped 531010a9a on every topic doc reviewed that day, which would have marked unchecked claims as verified. | P1 (fields, the meaning of verified, a baseline derived from git, doc-text edits flagged); batch H replaces seed item 2. |
| R3 | Keep the existing normative sources, add source and precedence to the topic map, never change intent to match a defect | ACCEPT. Rev 2's evidence list also called the DLQ contract a "wrong document"; it is now a defect plus a contract gap. | "Normative sources", F2, P4, evidence list. |
| R4 | Critical invariants need adequate evidence, not a fresh code read in every audit | ACCEPT | P5 "Critical invariants" and "When code is read". |
| R5 | Separate confirmed misses from optional ones; pin a revision without invalidating every branch behind main | ACCEPT. The replay confirmed items 1, 2, 5 and 6; items 4 and 7a can't be found from a diff; item 9 is history. | Audit table "Class" column, acceptance criterion 1, P5 "Pin". |
| Q5 | Weekly light audit plus retro spot checks | ACCEPT as a recommendation, hung on the existing weekly close so no phase is added | Owner question 5. |

Also corrected in rev 3: rev 2's X25 said "monitoring already records tokens per run". It doesn't. It records duration and a unitless cost proxy, so the token figures in the effort table are estimates.

## Rev 2: response to the first external review (2026-11-07), record only

Source: the first external review (`docs_as_review_source_plan_review.md`). The review file was removed once its points were dispositioned; its text is in git at d1fa1263c. Verdict: approve with changes. The requirements now live in the sections above. This table records the decision made on each suggestion.

| # | Suggestion | Disposition |
|---|---|---|
| X1 | Freshness is not correctness | ACCEPT (P1) |
| X2 | Four stored verification states | PARTIAL: none stored; derived (P1) |
| X3 | Provenance | ACCEPT light: `verified_by` (P1) |
| X4 | Staged indirect impact | PARTIAL: stage 1 is paths and symbols, stage 2 is graphify importers and mechanisms.yaml (F1); stage 3 DEFERRED |
| X5 | Risk-triggered code inspection | ACCEPT (P5) |
| X6 | Docs audit vs implementation audit | ACCEPT (P5) |
| X7 | New specification layer | PARTIAL: authority order yes, new folder no ("Normative sources") |
| X8 | A defect never triggers a spec change | ACCEPT ("Normative sources", F2) |
| X9 | F1 searches canonical refs and dependencies; required/candidate/excluded | ACCEPT (F1) |
| X10 | Keep explanation, normative and history edits distinct | ACCEPT (F2) |
| X11 | F3 escalates by risk | PARTIAL: advisory, critical first (F3) |
| X12 | Equal doc obligations on every close path | ACCEPT (F4) |
| X13 | F5 only behaviour-bearing comments | ACCEPT (F5) |
| X14 | P2 revision and counting rules | ACCEPT (P2) |
| X15 | Limits lifecycle | ACCEPT (P3) |
| X16 | Urgent doc-only PRs | REJECT premise: a doc-fix ticket can ship alone |
| X17 | Canonical source per fact | ACCEPT (P4) |
| X18 | Same-change tests are weaker evidence | ACCEPT (P5) |
| X19 | Confirm parity-ledger counts | ACCEPT (P2) |
| X20 | Weekly audit plus spot checks | ACCEPT as recommended in Q5 (rev 3) |
| X21 | Baseline discipline, renames, deletes | ACCEPT (P1) |
| X22 | Priority ordering | ACCEPT (seed batches) |
| X23 | Replay known misses | ACCEPT, restricted to confirmed misses (acceptance criterion 1) |
| X24 | Acceptance criteria | ACCEPT trimmed ("Acceptance criteria") |
| X25 | Measure context use | DEFER: judge by missed findings first. Monitoring has no token data (rev 3 correction). |
| X26 | Q2: `docs/architecture/` | ACCEPT |
| X27 | Q3 CLAUDE.md wording | ACCEPT wording (P5); needs your direct OK |
| X28 | Lead dispatches | REJECT premise: lead sends findings; the owner dispatches |
| X29 | Its 8 questions | ANSWERED. 1-2: the normative sources ("Normative sources"). 3: today nothing declares a doc verified. 4: no gate separates stale from never-validated. 5: yes, graphify and `mechanisms.yaml`. 6: the critical set is in P5. 7: no; a missing `test_path` can't be told from a missing test. 8: rpg-designer, through the world-rules catalog and `intentional_divergences.md`. Answers 3-8 are from my knowledge of the workflow, not re-read. |
