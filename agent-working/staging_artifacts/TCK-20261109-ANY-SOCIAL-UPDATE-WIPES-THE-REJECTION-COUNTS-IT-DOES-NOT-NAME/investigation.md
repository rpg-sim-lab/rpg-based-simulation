---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261109-ANY-SOCIAL-UPDATE-WIPES-THE-REJECTION-COUNTS-IT-DOES-NOT-NAME
artifact_type: investigation
phase: inprogress
date: 2026-11-11
tags: []
---

# Investigation

## The defect (read on origin/main 5c6990e51)
`src/systems/social_systems/relationships.py:133` (`RelationshipService.process_update`) ends its `replace(social, ...)` with
`rejection_count={k: social.rejection_count.get(k, 0) + v for k, v in update.rejection_increment.items()}`.
The result holds only the keys named in this update's increment. Every applied `SocialUpdate` therefore drops every other offerer's count, and a trust-only or familiarity-only update (empty increment) empties the dict.

## Writers and reader
- Writers: five rejection paths in `src/engine/domain/core_actions.py` (:206, :279, :354, :460, :528), each `SocialUpdate(rejection_increment={entity.id: 1}, last_offer_tick_set=current_tick)`.
- Reader: `src/systems/social_systems/appraisal.py:125`, `_appraise_recruitment`: penalty `min(0.5, count * 0.1)`; the loyalty acceptance at trust >= 0.9 also needs penalty < 0.2 (so it bites after 2 rejections once counts are kept).
- State: `SocialComponent.rejection_count` (`src/core/models/social.py:58`), in the canonical dict at `src/core/state.py:974`.

## F2: the merge
`SocialUpdate.merge` (`src/core/updates.py:385`) builds `rejection_increment={**self.rejection_increment, **other.rejection_increment}`, last writer per key, so two same-tick rejections from one offerer count once. `is_noop` (:340) already treats a non-empty increment as non-noop.

## Ruling (rpg-designer, 2026-11-09, in the ticket's Implementation Notes)
Bug Fix, not intended. Keying (`candidate.rejection_count[offerer]`) stays. Merge sums this field only; familiarity, debt, fear and salience stay last-writer-wins. Decay is out: counts are lifetime, bounded by the 0.5 cap (5 rejections); the window is TCK-20261109-RECRUITMENT-FATIGUE-HAS-NO-RECENT-WINDOW. `last_offer_tick` is per subject, not per offerer, so it cannot be the window. A divergence entry only if the paired measurement moves anything.

## Existing coverage and parity
`tests/unit/social/test_domain_7_social.py::test_social_fatigue` seeds `rejection_count={10: 3}` and reads the penalty. No SOC parity entry names social fatigue; SOC-263 (canonical hash) lists rejection_count as hashed state. Plan: add one entry (SOC-280), citing the new test.
