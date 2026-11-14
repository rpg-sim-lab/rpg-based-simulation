---
status: historical
layer: world
authority: P2
audience: agent
artifact_type: investigation
ticket_id: TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES
phase: done
date: 2026-11-14
tags: [world]
---

# rpg-designer ruling, 2026-11-14 (session message), relayed by rpg-planner.
# Ticket: TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES. The reference law is ENV-06 (environment.md:174-187, owner decision 10, 2026-10-05).

(a) NO SPY.

(b) DOCS-ONLY. Sort every claim three ways.
1) SUPERSEDED by ENV-06: rewrite, don't just annotate.
   - docs/world/ecology_and_calamity_contract.md:79 ("Hero death ... raises ... +0.05")
   - docs/world/threat_and_consequences_contract.md:55 ("calamity_intensity reduced" on a boss defeat)
   Replace each with:
   "Superseded by ENV-06 (owner decision 10, 2026-10-05): calamity intensity is the escalation of sustained instability; no single event (a hero's death, a boss defeat) changes it directly. The ENV-06 producer is not built yet; in current play calamity_intensity is 0.0 in every region (TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES). CalamityService.apply_calamity_consequences (+0.05 per hero death) is unwired legacy, kept only behind its architecture pin."
2) ENV-06 LAW with no code:
   - ecology_and_calamity_contract.md:92 ("intensity decays naturally"): keep it, and add "(ENV-06; not built: no decay code exists, and in current play intensity is 0.0 everywhere.)"
3) CONSUMERS: correct as code, inert in play. Add one note per location, in the #883 shape:
   - Bible 05:494, :127, :351; docs/world/home_exile_refugee_contract.md:69-93; the transformation requirements (wherever they're documented).
   - Note: "Current play: calamity_intensity has no producer (ENV-06 not built) and is 0.0 in every region, so this does not trigger in play (TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES)."
   - For the drain formula (05:127), say it reduces to plain hazard.

LEDGER (SOC-280 pattern), via tools/parity_ledger_writer.py ONLY:
- WORLD-105, WORLD-029, WORLD-060, WORLD-063, WORLD-121 and WORLD-DISPLACE-001 STAY verified, each with a support_boundary: "Inert in play (TCK-20260914-CALAMITY-INTENSITY-PRODUCER-NEVER-FIRES): calamity_intensity has no producer (the ENV-06 producer is not built; apply_calamity_consequences has no caller), so it is 0.0 in every region and this branch never triggers in play."
- WORLD-084 stays divergent. Append to its divergence_note: "The intended producer is ENV-06's sustained-instability escalation (owner decision 10, 2026-10-05), not this per-hero-death method; this method stays unwired by design."
- INFRA-258/246: no change unless their text claims intensity is non-zero in play. CHECK, and send the line to rpg-planner if it does.
- registries/mechanisms.yaml calamity_intensity stays orphan. Add the ENV-06 pointer to its note if it lacks one; send the before/after to rpg-planner for the designer first.

(c) CLOSE as docs-only; don't re-scope.
- If no ticket exists for the ENV-06 producer, open a todo at P2 naming owner decision 10 and the sequence after TCK-20260914-LAIR-REGION-TRAUMA-NEVER-ACCUMULATES. Its dispatch is the owner's, when LAIR lands.
- The architecture pin tests/architecture/test_calamity_intensity_producer_unwired.py stays. Its docstring should cite ENV-06. NOTE (rpg-planner): tests/architecture/** is testing-planner's path. Don't edit it; rpg-planner routes it.
