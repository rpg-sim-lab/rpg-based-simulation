---
status: historical
layer: ai
authority: P2
audience: agent
ticket_id: TCK-20261117-A-SUBJECT-RE-CHOOSES-THE-TARGET-IT-JUST-GAVE-UP-ON
artifact_type: investigation
tags: []
---

# Investigation

Written at close (2026-11-22) from the executed evidence of this branch; the ticket was built from the rpg-designer drafts (.claude/handover/drafts/rpg-designer-f2-giveup-memory.md, v2.2 / v2.2a) and rulings relayed by rpg-planner, so no pre-implementation staging artifacts existed.

Facts, labelled. EXECUTED: the stalemate own-job run (S9 #715 6947037311) found that after a way-round give-up the given-up target is chosen again within 200 ticks (crowded 17/17 subjects, flw 37/38, up 20/20). EXECUTED: the 300-tick smoke at 70ae7c4a2 and the pairing run of 0bfa0f6bb traced the remaining G1 / G1-held rows to one race inside a tick: the collection phase vets a tile open (nothing filed yet) and sets it, the fused pass then files or refuses it and adds a typed clear, and in the merged update the set wins over the clear (`NavigationPatch.apply`). The same race existed with a give-up record in place of a suppression clear. The fix generalises the apply rule to anchors (the record's, the pass's refusal, the pass's filing). INSPECTED: the work queue had no tier for a pending give-up record and the fast path never consumes one (a record outlived its window, G4).
Results (EXECUTED, post-fix full run, fixtree_v16, 3 cells x 5000t): G1-held 0/2/0, G1 0/2/0 (only the 2 flw own-tile holds), G3 1/6/12, all other bars 0; against the 0bfa0f6bb full run G1-held 9/5/7, G1 0/2/1, G3 2/6/4; against attempt 2 G1-held 2584/6938/676, G1 247/1993/361; perf -3.2%. The flw final hash equals the 0bfa0f6bb run's: an INFERENCE only (no subject positions in the rows). tactical_hold 0 calls (covered statically by G6). Queue tier counts and "A'' fired" are NOT MEASURED.
