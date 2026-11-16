# Implementation Sequence: ai-first-sdlc-evolution

Epic `TCK-20261031-EPIC-AI-FIRST-SDLC-EVOLUTION`, filed by agent-working-planner on dispatch from agent-working-designer, 2026-10-31. Plan: `docs/plans/agent_infrastructure/AI_FIRST_SDLC_ARCHITECTURE_EVOLUTION_PLAN.md`, section 38 for dependencies. Owner decisions: #715 6529263880.

## Order

1. TCK-20261031-SDLC-PLAN-DOCUMENTS-LAND: first PR, docs only. Everything below cites these files.
2. TCK-20261031-SDLC-E6B-THROWAWAY-REPO-GITHUB-BEHAVIOURS: the owner creates the machine account and repo first, as its own ask. First among the authority work, because OD-3's M1 depends on it.
3. Parallel after 1:
   - TCK-20261031-SDLC-HAND-PATH-OFFICIAL-AND-BASELINES-FROZEN (Phase 0)
   - TCK-20261031-SDLC-RULESET-EXPORT-AND-LOGIN-ASSUMPTION-INVENTORY (read-only)
   - TCK-20261031-SDLC-R0-INVENTORY-AND-BASELINE-TAGS (tag push has its own ask)
   - TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION
   - TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY (Phase 5, independent)
4. BLOCKED, each with its own owner ask:
   - TCK-20261031-SDLC-MACHINE-USER-AND-OWNER-CREDENTIAL-REMOVAL
   - TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION

## Rescoped 2026-11-15 (owner, #715 6889309909, 6889318166)

Done: TCK-20261031-SDLC-PLAN-DOCUMENTS-LAND (#794); TCK-20261031-SDLC-HAND-PATH-OFFICIAL-AND-BASELINES-FROZEN, TCK-20261031-SDLC-RULESET-EXPORT-AND-LOGIN-ASSUMPTION-INVENTORY and TCK-20261031-SDLC-R0-INVENTORY-AND-BASELINE-TAGS (#796); TCK-20261031-SDLC-GUARD-PAYLOADS-AND-SECRET-REDACTION and TCK-20261031-SDLC-PLAN-REVIEW-FIXES-AND-EVIDENCE (#800). The live order from here, after the ticket view epic (P3c and the backlog view) lands:

1. TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY (Phase 5). Its 11-15 recheck is in the ticket.
2. TCK-20261115-SDLC-BASELINE-TAG-RULESET. The owner applies it, and it can go any time on its own ask.
3. agent-working-designer brings OD-4, OD-5, OD-6, OD-11, OD-12 and OD-13 to the owner. Phases 2-4 are cut after the owner decides.

Deferred, out of live scope until the owner reopens them:
- TCK-20261031-SDLC-MACHINE-USER-AND-OWNER-CREDENTIAL-REMOVAL;
- TCK-20261031-SDLC-E6B-THROWAWAY-REPO-GITHUB-BEHAVIOURS;
- TCK-20261031-SDLC-RULESET-M1-AND-TAG-PROTECTION (the M1 part);
- R1-R5.

## Phases 2 and 3 filed 2026-11-16 (owner OD decisions, #715 6910853925)

Filing only. Dispatch is a separate owner go. Phase 1 is deferred, so "required" means required by owner practice.

Dispatch order:
1. TCK-20261116-SDLC-CLOSE-CHECK-REPORT-ONLY-GATE-JOB (Phase 2, P2), first. It is report-only and covers the three OD-4 layers, the test-scope floor line and the OD-12 two-PR detection line. It also runs the E1-replay over 50 merged closing PRs, counting the pipeline-only checks each hand close lacked.
2. TCK-20261116-SDLC-CLOSURE-RECORD-AND-EVIDENCE-LAYERS (Phase 3, P2), after 1. It depends on 1 only through close-check condition 6, which it switches on. It covers L1, L2 and L3 (OD-11), plus E5.

Independent, any time:
- TCK-20261116-SDLC-WORK-CLOSE-CLI (Phase 2, P3): the one-step close command. Its CLAUDE.md pointer needs the owner's direct OK.
- TCK-20261116-SDLC-ATTRIBUTION-FIELDS-AND-COORDINATION-METRICS (Phase 3, P3): tool-call and work-item ids, provenance labels, SessionEnd, and coordination metrics.
- TCK-20261116-SDLC-CODEX-TRACK-MARKED-LEGACY (OD-6, hotfix): marks the track as legacy support, and splits the CI lane only if it also runs tests/agent_orchestration.

## Docs-truth track filed 2026-11-16 (owner #715 6911224913, 6911534263; plan "Docs-truth track")

Filing only, all P3 and behind RPG (#715 6911759453). Dispatch is a separate owner go. Order:
1. TCK-20261116-DOC-CITATION-RESOLVER-REPORT-ONLY and TCK-20261116-DOC-CLASSIFICATION-LIST have no prerequisite.
2. In rpg's lane, filed by rpg-planner-ubuntu: TCK-20261116-THREE-PARITY-ROWS-CITE-A-TEST-THAT-DOES-NOT-EXIST, then TCK-20261116-PARITY-TEST-PATH-BECOMES-A-LIST (also gated on rpg-planner (u24)'s yes on the schema shape); and TCK-20261116-BRAINSTORM-DOCUMENTS-WITHOUT-A-STATUS-GET-ONE, after the classification list.
3. TCK-20261116-PARITY-NEW-ROW-TEST-PATH-RATCHET-REPORT-ONLY, after TCK-20261116-PARITY-TEST-PATH-BECOMES-A-LIST.
4. TCK-20261116-CHANGED-CODE-CHECK-REPORT-ONLY-WITH-PROOF-ESCAPE and TCK-20261116-FRESHNESS-STAMPS-REPORT-ONLY, after the resolver has run clean.

Already filed elsewhere: the knowledge-gateway docs move, TCK-20261116-THIRTEEN-DEAD-KNOWLEDGE-GATEWAY-DOCS-MOVE-TO-THE-ARCHIVE, in rpg's lane. Search ranking is Phase 5 item 2 in TCK-20261031-SDLC-CONTEXT-AND-SESSION-RELIABILITY. The prose-reading sample is held: `agent-working/stored_artifacts/sdlc-decisions/prose_sample_draw_and_protocol.md`.

## Not cut yet

- Phase 4: OD-5 is decided (#715 6911091662): option A with both conditions. TCK-20261116-SDLC-RETIRE-PIPELINE-WORKFLOWS is filed BLOCKED. Its gate: the close check has run 2 weeks carrying the test-scope floor line and the architecture-verdict line (the clock starts on the first day it carries both), Phase 3 has landed, and the R0 tags cover the files. Dispatch then needs an owner go.
- R1 stays deferred.

## Rules

- No credential or ruleset change runs without its own owner ask, by ticket.
- Credential details stay out of committed files, tickets and public comments (#715 6528807751).
- Pushes, tags and merges are the owner's yes, through lead-planner.
