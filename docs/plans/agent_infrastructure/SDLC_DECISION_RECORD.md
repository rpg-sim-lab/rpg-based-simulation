---
status: active
layer: ai
authority: P2
audience: agent
date: 2026-10-31
tags: [ai, governance, delivery, planning]
---

# AI-First SDLC: Decision Record

What the owner has decided about `AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md` (section 6), and what they have not. The plan's "Recommended" column is a recommendation, not a decision. A row reads **decided** only when it matches what an owner comment says, in that comment's words; where the plan and a comment differ, the comment wins. Plan and summary read at `1ccaba303`.

Sources (all on issue #715, the approvals log):

- **A** = comment 6529263880, owner answer given in the lead-planner terminal on 2026-10-31, recorded by lead-planner.
- **B** = comment 6529808776, owner answers given in the agent-working-designer terminal on 2026-10-30T17:55Z, recorded by lead-planner.

## Decided

| ID | Decision | Date | Source | Exact scope |
|---|---|---|---|---|
| OD-1 | The hand/batch path is the official model | 2026-10-31 | A | Yes. Does not retire the pipeline (that is OD-5). |
| OD-2 | A machine user for agents | 2026-10-31 | A | Yes ("machine user for agents; owner credentials off both hosts, old tokens revoked"), with OD-10. No credential change is authorised yet. |
| OD-10 | Where owner credentials live | 2026-10-31 | A | Yes, with OD-2 (same wording). No credential change is authorised yet. |
| OD-3 | Merge model | 2026-10-31 | A | **M1**: keep owner-only merge via the `update` rule, **subject to E6b confirming it**. No ruleset change is authorised yet. |
| OD-14 | Security rollback | 2026-10-31 | A | Yes: "safe rollback, agents never regain the owner token". |
| OD-15 | Freeze baselines before retirement | 2026-10-31 | A | Yes: "freeze baselines as tags". A tag push is a separate owner ask. |

Decided, but not an OD:

| Item | Date | Source | Exact scope |
|---|---|---|---|
| E6b | 2026-10-31 | A | Yes: a throwaway public repo test of GitHub behaviours; no production settings touched. |
| Audit document | 2026-10-30 | B | "Generalise, delete branch later": the docs PR generalises the credential details in the audit before it lands on main; the branch `agent-working-designer-u24-sdlc-plan-handover` is deleted after the docs PR, on the owner's own command. |
| E6b identity | 2026-10-30 | B | "Create the machine user now": the owner creates the account themself, added only to a throwaway repo, with a token that cannot reach this repo; it stays out of this repo until the Phase 1 ask. |

**No credential or ruleset change on this repository is authorised** by A or B. Execution comes later by ticket, each with its own ask.

## 2026-11-15: epic rescoped

Sources: **C** = #715 6889309909 (owner's exact words) and **D** = #715 6889318166 (owner's AskUserQuestion answers). Both were recorded by lead-planner on 2026-11-15.

| Item | Decision | Source | Exact scope |
|---|---|---|---|
| Machine account and credential removal (OD-2, OD-10 execution) | Deferred ("for now", so not dropped) | C, D | "I think we can ignore this for now, complete the epic without 'Agents get their own non-admin machine account, and your credentials leave both hosts.'" OD-2 and OD-10 stay decided; nothing executes them. |
| E6b and the M1 merge rule (OD-3 execution) | Deferred | D | "Drop E6b, keep tag ruleset": E6b and M1 are deferred with the machine account. OD-3 stays M1 on paper. |
| Tag ruleset for the baseline tags | Kept; the owner applies it | D | Only the tag ruleset protecting the 4 baseline tags stays. |
| Order | Phase 5, then Phases 2-4 | D | Phase 5 is dispatched. agent-working-designer brings OD-4/5/6/11/12/13 with options and a recommendation; Phases 2-4 are filed after the owner decides. R1-R5 stay deferred. |
| Timing | After the ticket view epic | D | "After the ticket view epic": once P3c and the backlog view land. |
| Stale input (a fact, not a decision) | Redo, don't reuse | repo settings | The repository has been owned by the rpg-sim-lab organization since 2026-11-12 (#715 6818960465). The plan's GitHub analysis assumes a personal repo, so it is redone for OD-13 and for any deferred item that reopens. |

This changes no row under Undecided below. In particular, OD-4, OD-5, OD-6, OD-11, OD-12 and OD-13 stay undecided, and go to the owner in agent-working-designer's option pack.

## 2026-11-16: OD-4, OD-6, OD-11, OD-12 and OD-13 decided; OD-5 not decided

Source: **E** = #715 6910853925, the owner's answers on agent-working-designer's option pack (first cut, 2026-11-16), recorded by lead-planner on 2026-11-16. The owner's exact words:

> "OD-4 - the test (deep layer testings, not just the project tests but the agent working gates.  OD-5 - we  can but need a strong evidences from both our project observation and research/studies, recommendations from people. OD-06 - if it cause no issue, keep it and mark as legacy support (provider-agnostic). OD-11 - OD-13 you can go with recommendations"

| ID | Decision | Source | Exact scope |
|---|---|---|---|
| OD-4 | Decided: the close check goes deep, beyond the project tests | E | The owner's words are above. **Reading, not the owner's words** (lead-planner's, confirmed by agent-working-designer): three layers, each reported on its own: (1) the project test lanes for the paths the PR touches; (2) the agent-working tool tests when `tools/` or the workflows change; (3) the gate ledger, with no unresolved blocking verdict (plan §28 condition 8). All are report-only first, and measured in the E1-replay. If the owner meant fewer layers, the others drop at the end of the report-only window. |
| OD-6 | Decided: keep the Codex / provider-neutral track, marked legacy | E | "if it cause no issue, keep it and mark as legacy support (provider-agnostic)". No removal. |
| OD-11 | Decided: the pack's recommendation | E | Three linked layers (L1 closure record, L2 derived view, L3 appended by week close), no database (plan §29a). |
| OD-12 | Decided: the pack's recommendation | E | Claims stay advisory. The gate job detects a ticket closed in two open PRs. The ref-per-ticket claim (option B) can come later. |
| OD-13 | Decided: the pack's recommendation | E | One always-run gate job. While M1 is deferred, "required" means required by owner practice, not enforced by a ruleset. |
| OD-5 | **Not decided** | E | Retiring the pipeline is acceptable only on "strong evidences from both our project observation and research/studies, recommendations from people". An evidence pack comes first (agent-working-designer). Phase 4 waits on it. |

Phases 2 and 3 are filed from E, as filings only: dispatch is a separate owner go (`agent-working/tickets/todos/ai-first-sdlc-evolution/SEQUENCE.md`). The Undecided table below still lists the 10-31 state. Rows decided in A, B, C, D or E override it.

## 2026-11-16 (later): OD-5 decided

Source: **F** = #715 6911091662, the owner's answers by AskUserQuestion on agent-working-designer's OD-5 evidence pack, recorded by lead-planner on 2026-11-16. The text below gives the options the owner chose, as lead-planner recorded them; it is not the owner's own words.

| ID | Decision | Source | Exact scope |
|---|---|---|---|
| OD-5 | Decided: option A, retire in Phase 4, with both conditions | F | Remove `implement-ticket.js` only after the OD-4 close check has run 2 weeks and carries (1) a mechanical test-scope floor and (2) an architecture verdict on `src`-touching PRs. Neither condition is waived. Baseline tags make removal recoverable. |
| `implement-epic.js` and the skill imitation | Decided: follow OD-5, removed together in Phase 4 | F | Not removed sooner and not kept. |

Not chosen: retiring with a condition waived; B (finish the native port); C (leave as is). The evidence is `agent-working/stored_artifacts/sdlc-decisions/od5_evidence_pack.md`. This supersedes the OD-5 row in the section above ("Not decided").

The "run 2 weeks" clock starts on the first day the check carries both conditions. A check that runs without them does not start the clock.

## Undecided

All of these read undecided as of 2026-10-31 (A and B both say so). Nothing below is decided by being listed in the plan, the summary or a ticket.

| ID | Decision (plan section 6 title) |
|---|---|
| OD-4 | What has to be machine-proven before a close |
| OD-5 | Retire `implement-ticket.js`, `implement-epic.js` and the skill imitation |
| OD-6 | Codex/provider-neutral track |
| OD-7 | Owner review load (follows OD-3) |
| OD-8 | A token/cost budget |
| OD-9 | Coordination target |
| OD-11 | Evidence lifecycle |
| OD-12 | Claim consistency |
| OD-13 | Required CI shape |
| OD-16 | Evaluation investment and execution |
| OD-17 | Evaluation framework |
| OD-18 | Scope of model comparisons |
| OD-19 | Advanced optimization |
| OD-20 | Promotion of an experimental result |
| OD-21 | Practical threshold and budget per stage |

## Where the plan's wording differs from the comments

- OD-2 and OD-10: the plan's table says the owner's credentials "leave agent-reachable storage"; comment A says "off both hosts". This record uses the comment's words.
- OD-14: the plan recommends "Suspend" publishing; comment A says "safe rollback, agents never regain the owner token". This record uses the comment's words.
