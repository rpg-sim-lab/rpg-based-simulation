---
content_type: doc
status: historical
layer: ai
authority: P2
audience: agent
tags: [ai, governance, delivery]
---

# Docs-truth plan: keep documents true, keep one home per fact

Draft by agent-working-designer, 2026-11-16, measured at origin/main db6b4579d unless stated. Not committed. Nothing is deleted or moved by this draft: every removal comes to the owner as a list first. Requests it answers: #715 6896608585 (stale and duplicated docs), the owner's two follow-ups (cleanup without "code only"; "kept true, not fewer" for RPG docs), and the views of lead-planner-u24, rpg-designer and rpg-planner (relayed by lead-planner).

## 1. What I measured, and what I got wrong first

| Measurement | Result | Source / limit |
|---|---|---|
| Corpus (git ls-files + line counts) | src 853 files / 138,495 lines; docs 1,316 / 529,049 (archive 462 / 172,230; plans 254 / 61,303); tickets 3,521 / 463,222; stored_artifacts 7,935 / 794,499 | reproduces lead-planner's figures at f94417e6f |
| What the search index holds | 17,502 chunks, about 19.6M characters. `docs/` is about 75% of it. `docs/archive` and `docs/lab` are never indexed; closed tickets are indexed by Request Summary only; stored investigations by their first 500 characters; the graph excludes docs, tickets and artifacts | `tools/knowledge_search.py` and `.graphifyignore`; chunk counts are from the main checkout's index, indicative only |
| Biggest default-index parts | `docs/plans` 4.7M characters (254 files; 171 active, 75 historical, 8 idea), `world_rules` 1.7M (78 authoritative), `brainstorm` 1.6M (19 active, 14 with no status), `guidelines` 0.8M, `audits` 0.7M | same index |
| Backticked repo paths in non-archive docs that no longer exist | 636 of 11,714 (5.4%) overall; 204 of 647 docs with any path have at least one dead path | script in section 6, path existence in `git ls-files` |
| Same, by area | plans 5%; guidelines 4%; audits 8%; mechanics 1.4%; world_rules 0.5%; engine 18% | |
| The engine outlier | 89 of the 110 dead paths in `docs/engine` are in 14 knowledge-gateway (KGMCP) documents; the rest of `docs/engine` is 5.8% (21 of 363) | the gateway code was extracted and archived in #147 (2026-09-08) |
| Symbol-level (function and class names that no longer exist) | **Discarded.** My check failed its positive control: it reported `WorldState`, `AdventureDecisionPhase` and `process_active_contracts` as missing, and all three exist in `src`. | see section 5 |

Corrections to what I told you earlier, so they do not harden:
- "Agents search 1.8M lines, mostly history" is not what the index does (section above): the history tier is already mostly out of the default index. The live problem is `docs/plans` and `docs/brainstorm` sitting in the default index with no status ranking.
- My earlier 101 "missing test file" parity rows was a parse error; the right number is 3 (rpg-planner).

What the path measure does and does not show. It finds references to files that are gone. It does not find a document that is wrong about a file that still exists; for that the project has no measurement yet, and I have not sampled it by reading documents (the owner's "sample how much narrates code that changed"). I recommend that as a bounded second step (section 4, P1), not guessed.

## 2. The proposals, with options and a recommendation

Each is a proposal to weigh, not a decision. Items marked UNMEASURED have no figure from me.

### P1. One home per kind of fact, and a status for every document
Rule: decisions live on #715 and in the decision records; status lives in the GitHub Project; rules that can be checked live as machine checks; game mechanics live in the Bible and engine contracts; a document that restates a fact owned elsewhere becomes a link. Every hand-written document is exactly one of: generated; checked against code in CI; dated and owned ("as of <sha>, owner <seat>"); or archived (lead-planner, items 4 and 6).
- Option A: write the rule and apply it only to new documents.
- Option B: A, plus a one-time classification of the existing documents by a script: status, last-touched, path-resolution result. A list, not a change.
- Option C: B, plus a CI report (not a gate) that lists documents with dead paths.
Recommendation: B first. It produces the owner's review list for free, and C follows once the report has run without surprises. A alone changes nothing for what already exists.
The CLAUDE.md wording that would carry the rule is a governing-file change and needs the owner's direct yes each time; I will draft exact before/after text only on request.

### P2. The cleanup lists (nothing removed until the owner approves a list)
Categories, with what I can already name:
- **Move out of the default index, keep in git:** documents whose own status is historical (75 in `docs/plans`, plus 13 historical documents under `docs/engine/contracts/knowledge_gateway_mcp/` and others). Smallest change: exclude `status: historical` from the default `search_docs` ranking, or index it as a cold tier searched only on request. Nothing is deleted. This is the largest effect on what agents read.
- **A concrete list now:** the 14 KGMCP documents (3,282 lines) under `docs/engine/contracts/`. Two are still `status: active` (`knowledge_gateway_mcp_contract.md`, `redaction_retention_policy.md`) and all 14 carry authority P1, but the code they describe was removed in #147. Option: mark the two active ones historical and move all 14 under `docs/archive/`, or leave them and add a one-line "code removed in #147" banner. Owner: whoever owns `docs/engine` (rpg-planner) and the KGMCP decision record; the move touches `docs/engine/**`, which is not in my owns.
- **Needs a decision on kind:** the 14 `docs/brainstorm` documents with no status; assign one or archive.
- **Generated, not hand-kept:** board.md content now duplicated by the GitHub Project (lead-planner's item 4): the lead's file; a pointer page.
Recommendation: send the owner the KGMCP list and the historical-plans rule first; they are measured and low risk. Other lists wait for P1's classification script.

### P3. A rule for new documents
"Record decisions and rules; never narrate code" (owner's framing). Narration the project already accepts as a different kind: generated tables, the parity ledger, the world-rules catalog. The rule is easy to state and hard to check by machine; the cheap check is P5's citation resolver, which catches the most common narration (a path or symbol). Recommendation: state the rule in the same wording as P1, check it only through P5.

### P4. REGISTRY.yaml generated in CI instead of committed
Lead-planner measured 6 re-syncs in one day (not re-measured by me; UNMEASURED). Before recommending this I would need to know who reads `docs/REGISTRY.yaml` locally: the search tooling, the done-checker, ticket tooling, and the post-merge hook. Options: (a) keep committed, accept the conflicts; (b) generate in CI and read it from a CI artifact or generate locally on demand; (c) keep committed but split by directory so merges conflict less. Recommendation: do the reader count first (a read-only grep over `tools/`), then choose. I do not recommend (b) before that count.

### P5. Keep the authoritative RPG documents true ("kept true, not fewer")
Authoritative set (rpg-designer): `docs/mechanics/`, `docs/engine/`, `docs/parity_ledger/*.yaml`, `docs/guidelines/intentional_divergences.md`, `docs/world_rules/`, `registries/mechanisms.yaml`. Not authoritative: brainstorm, plans, audits, archive, tickets, stored artifacts.
Four checks, in the order the lanes and my measurements support:
1. **Citations resolve** (cheapest, lead-planner-u24 and rpg-planner both support). Resolve files, functions, flags and test paths, not line numbers; a line number may sit beside a symbol, and only the symbol is checked (rpg-designer). Baseline now: mechanics 1.4% dead paths, world_rules 0.5%, engine 5.8% excluding KGMCP. There are 538 file:line citations (rpg-planner; I reproduced 538); convert to symbol citations as chapters are touched. **My symbol measurement failed its control, so the resolver must be built on the AST (parse `def` and `class` properly) and ship with a positive and a negative control before it is believed.** That failure is itself evidence for the rpg-planner caution that this tool needs care.
2. **Changed-code check required for `implemented_by` code** (rpg-planner supports with conditions): 99 of 110 mechanisms cite 172 files; over the last 150 first-parent merges 14 of 36 `src`-touching merges would fire, 1-12 findings each (rpg-planner's replay, not re-run). The "no behaviour change" escape needs proof, not a bare reason: hash-neutral proof (pinned cell, world, seed, ticks, both final hashes equal), self-certifying; or, for annotation-only changes, rpg-designer's sign-off on the ticket, with rpg-planner checking the proof (lead-planner-u24's combination). One finding per file with its mechanism list.
3. **"Verified at <sha>, owner <seat>" stamps:** flag a stamp only when files the chapter cites change after the stamp (rpg-designer, rpg-planner). Both lanes and lead-planner-u24 warn that stamping on any code change will fire on most RPG PRs. Recommendation: report-only permanently, or drop. Check the Bible's existing "Certified Level 1" claim first so the stamp is not a second source of truth.
4. **Parity rows with status `verified` need a CI-run test.** 1,961 rows are `verified`; 1,210 have no `test_path` (reproduced). Day-one downgrade would be about 1,213 (62%). Use a ratchet instead: rows added or changed after cutover need a CI-run `test_path`; the 1,210 are burned down by subsystem, P0 first, under `TCK-20261114-PARITY-LEDGER-TEST-PATH-ERRORS-REMAIN-IN-SEVEN-FILES` (the plan does not take them over). Rows resting on slow or integration tests CI does not run get `verified_offline`, not "missing"; only a test that is gone or no longer collects downgrades outright (3 rows today). A resolver for `test_path` has to split on `;`, strip backticks, and accept directories and non-Python tests; my own re-parse produced 21 false misses from `+` separators and prose in the field. **Prerequisite:** make `test_path` a list of paths with prose moved to a note field, or the resolver cannot be required.
Rollout (agreed by the lanes): report-only for 2 weeks with counts of how often each check fires and why, then the owner picks which become required (owner practice, while M1 is deferred). Nothing flips to required while HOLD stage 2 or the D1 measurement PRs are in flight; rpg-planner says when that window clears. The simplest option is checks 1 and 2 only.
Ownership: content and `mechanisms.yaml` are rpg's; the check tools are agent-working's and testing's. Any change to `registries/mechanisms.yaml` goes to rpg-planner as exact before/after, never from me.

### P6. Coordination items from the original request (heavy-slot lock, fewer open seats, lighter path for no-code changes)
These are not about documents. I have no measurement for any of them (UNMEASURED) and do not fold them into this plan: the heavy-slot lock is a small tool and fits agent-working; fewer open seats is a lead habit; the lighter path for no-code changes collides with the monitoring-coverage rules and needs the owner's call. Recommendation: separate short options page if the owner wants it, after P1-P5.

## 3. Order
1. P5 check 1 (citation resolver, report-only) and the KGMCP list: measured, low risk.
2. P1 classification script (a list for the owner).
3. P2's historical-plans exclusion from the default ranking, after the owner approves the list.
4. P5 checks 2 and 4 in report-only, after check 1 has run clean for 2 weeks; then the `test_path` structure change.
5. P4 after the reader count. P3 and the CLAUDE.md wording after P1.

## 4. What I need from the owner, and what I need to measure
Owner: approve or amend the KGMCP list (P2); say whether historical documents should drop out of default ranking; say which of P5's four checks to run report-only first.
Measure before the next draft: a bounded reading sample of 20-30 authoritative and plan documents, to estimate how many are wrong about a file that still exists (the path measure cannot see that); the P4 reader count; the REGISTRY re-sync count at a named ref.

## 5. Where the measurement failed (so it is not repeated)
The symbol check built its list of known names from `def`, `class` and assignment lines in `src`, `tools` and `tests`, and still reported three names missing that exist. I did not find the cause in this session (candidates: names defined in nested scopes or by decorators; names that appear only in `.js` or `.ts`; my regex). Because it failed a positive control I discarded every symbol number. Do not cite them.

## 6. How the path measure was made (reproducible)
Backticked strings starting with `src/`, `tools/`, `tests/`, `.claude/`, `.github/`, `registries/`, `docs/`, `frontend/` or `scripts/` (optionally `:<line>`), skipping any with a glob character, in every tracked `docs/**/*.md` except `docs/archive/`, checked against `git ls-files` and its parent directories. Limits: it treats a path to a generated or untracked file as dead, and it cannot see paths written without backticks. Positive control: the KGMCP documents point at `tools/knowledge_gateway_mcp.py`, deleted in #147, and the check flagged it.

## 7. Added 2026-11-16: constants sample, and the owner's decisions (#715 6911224913, 6911534263)

### Owner decisions on this plan
- KGMCP: archive the other 13 documents, keep `redaction_retention_policy.md` in place as active and fix its dead paths; `evidence_cache_identity_contract.md` moves with the 13 (option B). Filing: rpg-planner via lead-planner-u24, one change with both lanes reviewing. Exact edits: TCK-20261116-THIRTEEN-DEAD-KNOWLEDGE-GATEWAY-DOCS-MOVE-TO-THE-ARCHIVE.
- Search ranking: historical plans and status-less brainstorm documents rank lower by default, still searchable; brainstorm documents get a status first.
- Doc-truth checks, all report-only and none blocking: the citation resolver (AST-based, with positive controls), the changed-code check (the escape needs proof), the parity `test_path` ratchet (`test_path` becomes a list first), and freshness stamps (dropped if noisy).
- Priority (#715 6911759453): RPG is the highest priority. This plan continues at lower priority and yields to any RPG review.

### The reading sample, as far as I did it
I did not read prose. I ran an automated constants check as a cheaper proxy: documented constants of the form `` `NAME` = 12 `` or `` `NAME = 12` `` in the listed areas, matched to a module-level numeric constant of the same name in `src/` or `tools/` (130 claims in total, at db6b4579d).

| Area | Claims | Name not found in code | Value differs from code |
|---|---|---|---|
| docs/mechanics | 23 | 0 | 0 |
| docs/world_rules | 1 | 0 | 0 |
| docs/engine | 16 | 10 | 1 (`MAX_PAYLOAD_BYTES` 8192 in a KGMCP comparison doc against 65536 in `tools/write_path_guard.py`) |
| docs/guidelines | 15 | 8 | 0 |
| docs/architecture | 10 | 2 | 0 |
| docs/performance | 7 | 6 | 0 |
| docs/plans | 58 | 26 | 3 (a point-in-time audit says `CARD_BUDGET_TOKENS` 460 and the code has 456; a KGMCP proposal repeats the 8192; a sign difference on `RIVAL_SENTIMENT_THRESHOLD` 0.8 against -0.8) |

What it supports, and the limits:
- The Bible's documented constants all match the code (23 of 23, none missing). That is the part of "kept true" where the evidence is good. It covers constants only, and only ones written in this backticked form.
- Where a name is not found in code, the cause is usually a proposal in a plan (names not yet built), a removed module (KGMCP), or a constant defined another way; I did not separate these. Do not read that column as rot.
- The three plan mismatches are a dated audit, an archived proposal and a sign; none is a live document going wrong.
- Positive control: the known-different case (`MAX_PAYLOAD_BYTES`, doc 8192 against code 65536) was caught. Negative control: the 23 mechanics claims all matched. The check is narrow and the sample small.
- A real reading sample of prose claims (what a function does, which order phases run in) is still not done. Recommended owner for the authoritative areas: rpg-designer, who owns the content, over 10 chapters drawn at random, each checked by the file the chapter cites. I will draw the sample list and the checking protocol if asked; I will not read the chapters for RPG, since RPG review has priority and the content is theirs.
