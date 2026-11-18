---
status: active
layer: world
authority: P1
audience: agent
artifact_type: investigation
ticket_id: TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND
phase: open
date: 2026-11-18
tags: []
---

# Reproduction mate gate: exact doc texts reversing the 2026-08-29 decoupling (rpg-designer-ubuntu, 2026-11-18, for rpg-designer's ruling BEFORE code)
- **Basis:**
  - Q-G3 (rpg-designer, relayed by lead-planner): the gate is an ACCEPTED MarriageState between the two, OR both directed sentiments >= `min_mutual_sentiment`; humanoids reference the FRIEND threshold constant;
  - the owner's "Marriage OR mutual affection" (#715);
  - reproduction design rev 2 (e5729d3f).
- **Before text:** from births head 02d327ba6 (rpg-ubuntu-wild-births-impl). I checked that each anchor occurs exactly once in its file at 02d327ba6.
- **Correction to the ask:** the "Marriage does not gate Reproduction" passage is NOT in ch07. It sits in **ch01:208-209** and **ch05:580-583**, and in two ledger entries (SOC-259, WORLD-122). ch07 and ch04 §8 only need a cross-reference, because the MARRIAGE contract row and its "Current play" note are where a reader looks for what a marriage does.
- **Interaction with B5:** ch05 §6's humanoid-path section (which holds :580-583) and WORLD-122 describe the removed `HumanoidReproductionService` path. B5 rewrites or retires them anyway.
  - Text 2 below is the paragraph the new births section carries in place of :580-583.
  - Text 6 is the retirement text for WORLD-122's marriage sentence, whatever B5 does with the rest of the entry.
- **Field names** (`mate_gate`, `min_mutual_sentiment`, `MarriageStatus.ACCEPTED`, `SocialBond.sentiment`) follow the design. If the implementer names them differently, the texts follow the code.

## 1. docs/mechanics/01_entity_anatomy.md:208-209
**Before:**
```
Reproduction (idea 32) is explicitly decoupled from Marriage (idea 33): no marriage/contract
precondition gates any part of this schema or its write path.
```
**After:**
```
This schema carries no marriage or contract field. Whether a pair may conceive is decided by the
species' declared mate gate (05, Births Law): for a species whose reproduction profile declares
`mate_gate: bond`, an ACCEPTED `MarriageState` between the two, or both directed
`SocialBond.sentiment` values at or above the profile's `min_mutual_sentiment`, passes the gate.
This reverses the 2026-08-29 decoupling of Reproduction (idea 32) from Marriage (idea 33);
see `docs/guidelines/intentional_divergences.md` 2.NNN.
```

## 2. docs/mechanics/05_world_evolution.md:580-583, the "Not marriage-gated" paragraph
**Before:**
```
**Not marriage-gated:** per the 2026-08-29 build-order decoupling of Marriage (idea 33) from
Reproduction (idea 32), this eligibility path never reads or checks any marriage-contract state
(`ContractKind.MARRIAGE`/`MarriageState`) — verified by an architecture-guard test
(`tests/unit/world/test_reproduction_humanoid_cadence.py`).
```
**After** (as the "Mate gate" paragraph of the births section B5 writes):
```
**Mate gate:** each reproduction profile declares `mate_gate`. With `none` (every non-humanoid
profile in M1), no social state is read. With `bond` (the humanoid profile), a pair passes only if,
at the conception tick, an ACCEPTED `MarriageState` joins the two (held by either party), or both
directed `SocialBond.sentiment` values (mother to mate and mate to mother) are at or above the
profile's `min_mutual_sentiment`. The humanoid value references
`RelationshipService.FRIEND_SENTIMENT_THRESHOLD`, not a copied number. These two reads are the
only social reads in births (Q18 is lifted for them alone); role, kind and occupation are never
read. **Current play:** nothing in play issues PROPOSE_MARRIAGE (07, Contract Kinds, Current
play), so the marriage arm is never reached and the sentiment arm decides. This reverses the
2026-08-29 decoupling of Marriage (idea 33) from Reproduction (idea 32); see
`docs/guidelines/intentional_divergences.md` 2.NNN.
```

## 3. docs/mechanics/07_social_political_dynamics.md:72, the MARRIAGE row of Contract Kinds
**Anchor (unique):** `Bigamy prevention and aging/duration thresholds are deliberately out of scope — see \`docs/mechanics/04_strategic_cognition.md\` §8 |`
**After** (the row ends):
```
Bigamy prevention and aging/duration thresholds are deliberately out of scope — see `docs/mechanics/04_strategic_cognition.md` §8. An ACCEPTED `MarriageState` also passes the reproduction mate gate of a species declaring `mate_gate: bond` (05, Births Law, Mate gate) |
```

## 4. docs/mechanics/07_social_political_dynamics.md:77, the "Current play (MERCHANT, TEAM_UP, TEACH, MARRIAGE, CLAN …)" note
**Anchor (unique):** `No clan exists in play: \`AuthoritativeState.clans\` starts empty and nothing creates one.`
**Insert directly after it**, in the same paragraph:
```
 Because no `MarriageState` is written in play, the marriage arm of the reproduction mate gate (05, Births Law, Mate gate) is never reached; the mutual-sentiment arm decides.
```

## 5. docs/mechanics/04_strategic_cognition.md:1074, the §8 "Current play" line
**Before:**
```
> **Current play.** Nothing in play issues PROPOSE_MARRIAGE, so this law does not run in play and no `MarriageState` is written (see 07, Contract Kinds, Current play).
```
**After:**
```
> **Current play.** Nothing in play issues PROPOSE_MARRIAGE, so this law does not run in play and no `MarriageState` is written (see 07, Contract Kinds, Current play). An ACCEPTED `MarriageState` is one arm of the reproduction mate gate (05, Births Law, Mate gate); that arm is unreached until something issues PROPOSE_MARRIAGE.
```

## 6. docs/parity_ledger/world_dynamics.yaml, WORLD-122 (:1985-1986)
**Before:**
```
    to the Natural-Creature sibling). This path is explicitly NOT gated on any marriage-contract
    state (2026-08-29 build-order decoupling of idea 32 from idea 33). On a successful
```
**After:**
```
    to the Natural-Creature sibling). This path was not gated on any marriage-contract state
    (2026-08-29 decoupling, reversed by the M1 births mate gate, divergence 2.NNN). On a successful
```
- B5 sets WORLD-122's status for the removed path. This text only stops the entry asserting a law that no longer holds.

## 7. docs/parity_ledger/social_narrative.yaml, SOC-259 (:3815-3818)
**Before:**
```
    SocialUpdate.bond_updates path. This is schema + builder plumbing only -- no reproduction
    trigger logic, no genetics wiring, and explicitly no marriage/contract precondition
    anywhere in the schema or its write path (Reproduction, idea 32, is decoupled
    from Marriage, idea 33, per the 2026-08-29 build-order decision).'
```
**After:**
```
    SocialUpdate.bond_updates path. This is schema + builder plumbing only -- no reproduction
    trigger logic, no genetics wiring, and no marriage/contract field in the schema or its
    write path. Whether a pair may conceive is the births mate gate's decision (SOC-NNN),
    which reverses the 2026-08-29 decoupling of idea 32 from idea 33 (divergence 2.NNN).'
```
- SOC-259's status stays `verified`, because the schema claim is unchanged.

## 8. docs/parity_ledger/social_narrative.yaml, NEW entry SOC-NNN, the births mate gate (next free SOC id at commit)
```
- id: SOC-NNN
  text: 'Reproduction mate gate (M1 births): a reproduction profile declares mate_gate none|bond.
    With none, conception reads no social state. With bond, a pair passes only if, at the conception
    tick, an ACCEPTED MarriageState joins the two (held by either party), or both directed
    SocialBond.sentiment values are >= the profile''s min_mutual_sentiment; the humanoid value
    references RelationshipService.FRIEND_SENTIMENT_THRESHOLD. Role, kind and occupation are never
    read. Nothing in play writes a MarriageState, so the marriage arm is unreached in play.'
  status: verified
  priority: P1
  legacy_evidence: null
  v2_evidence: <the gate function in src/world/births.py and the profile schema fields, as implemented>
  proof_type: regression
  test_path: <the implementer's unit test proving both arms and the none case, e.g. tests/unit/world/test_births.py::test_bond_gate_passes_on_accepted_marriage_or_mutual_sentiment_and_none_reads_nothing>
  divergence_note: 'Reverses the 2026-08-29 decoupling of Reproduction (idea 32) from Marriage (idea 33); divergence 2.NNN.'
  support_boundary: 'The marriage arm is not reachable in play: nothing issues PROPOSE_MARRIAGE (TCK-20261113-FIVE-SOCIAL-ACTION-KINDS-MAY-HAVE-NO-ISSUER-IN-PLAY).'
```
- `v2_evidence` and `test_path` are filled from the code when it lands. A P1 entry needs a passing test_path.

## 9. docs/guidelines/intentional_divergences.md, NEW row 2.NNN (the next free number at commit; 2.212 is the highest on main at 99a83adc9)
```
### 2.NNN People Conceive Only When Married Or Fond Of Each Other: The Reproduction Mate Gate Reverses The 2026-08-29 Decoupling Of Marriage From Reproduction (ch05 Births Law, Mate gate; ch01 Birth Record; ch07 Contract Kinds MARRIAGE; SOC-259; SOC-NNN; WORLD-122; TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND)
- **Behavior**: Before: per the 2026-08-29 build-order decision (TCK-20260902-MARRIAGE-PROPOSAL-CONTRACT), no marriage or social state gated any reproduction path. After: a reproduction profile declares `mate_gate`. `none` reads nothing. `bond` (the humanoid profile in M1) lets a pair conceive only if an ACCEPTED `MarriageState` joins them, or both directed `SocialBond.sentiment` values are at or above `min_mutual_sentiment`, which for humanoids references the FRIEND threshold constant.
- **Disclosed**: (1) Nothing in play issues PROPOSE_MARRIAGE, so the marriage arm is unreached and the sentiment arm decides. (2) With the compressed human gestation (content `gestation_ticks`, 2400 ticks = one in-game day at commit; compressed, order kept, owner #715 6966994323), 1000-tick runs give 0 human births by construction, and 5000-tick runs were predicted at 0-3 per world and seed before data. (3) Wild kinds (`mate_gate: none`) are unchanged by this row. (4) The threshold is a content value, report-only, and deferred to TCK-20261118-BIRTHS-BALANCING-PASS.
- **Rationale**: **Intentional Gameplay Change**: the owner ruled (#715 6966994323, 2026-11-18) that people need marriage or high enough mutual affection to have children, while wild animals do not.
- **Verification**: <the SOC-NNN test_path>; plus the own-job HARD row G5 (no conception on a `bond` species without an accepted marriage or both sentiments at or above the threshold; no gate read on a `none` species).
```

## Pre-bind check
- No Rule ID changes. The ch01, ch04, ch05 and ch07 texts, the two ledger edits, the new ledger entry and the divergence row are all rpg-designer's to rule BEFORE code (Q-G3).
- If ch04 §8 or ch07 belong to another owner's review, rpg-designer says so.

## Ruling (rpg-designer, relayed by lead-planner, 2026-11-18): APPROVED with 2 edits, both applied above
- Edit 1: divergence item (2) no longer hard-codes the gestation value; it cites content and #715 6966994323.
- Edit 2: the Rationale cites #715 6966994323.
- **At commit:**
  - skip 2.213 and 2.214, which are reserved;
  - SOC-NNN becomes `verified` only once its test passes;
  - FRIEND_SENTIMENT_THRESHOLD = 0.8 (relationships.py:21).
- ch04 and ch07 need no other review.
- **For the maturation ticket, not M1:** parent bonds seed at 0.8, which equals FRIEND, so that ticket needs a kin exclusion on mate eligibility.
