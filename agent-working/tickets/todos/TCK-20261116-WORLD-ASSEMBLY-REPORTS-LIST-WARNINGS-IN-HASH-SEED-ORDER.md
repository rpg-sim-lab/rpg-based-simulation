---
status: active
layer: world
authority: P2
audience: agent
ticket_id: TCK-20261116-WORLD-ASSEMBLY-REPORTS-LIST-WARNINGS-IN-HASH-SEED-ORDER
phase: open
date: 2026-11-16
tags: [determinism]
---

# TCK-20261116-WORLD-ASSEMBLY-REPORTS-LIST-WARNINGS-IN-HASH-SEED-ORDER

## Title
The generated world's assembly_report.json and validation_report.json list their warnings in an order that changes with PYTHONHASHSEED, so the same seed gives byte-different reports in two processes

## Status
OPEN

## Tier
hotfix

## Type
bug

## Priority
P3

## Request Summary
rpg-implementer-ubuntu found this while proving that the world-generator fix (TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED, branch rpg-ubuntu-generator-resource-order, head da0ab518d) leaves `ProceduralCompositionGenerator`'s output unmoved.

The check generated seeds 42, 7 and 12345 at PYTHONHASHSEED 0 and 1, on main db6b4579d and on the fix. Main and fix were identical at each hash seed. Across hash seeds, though, `resolved/assembly_report.json` and `validation_report.json` list the same warnings in a different order. `world.yaml` and the provenance manifest don't vary. Divergence 2.145 and that ticket's Known gaps disclose it; it isn't fixed there.

The world content doesn't change, so this is report determinism, not simulation state. Still, two runs of one seed can't be compared byte for byte, and a report diff shows noise. Filed by rpg-planner-ubuntu. Filing only; dispatch needs an owner go.

## Scope
1. Find where the two reports collect their warnings. Trace the producer, not a name match. Find the unordered source: a set, a dict built from one, or a set-ordered walk.
2. Emit the warnings in a stable order. Prefer the order of the check that raised them, if that order is deterministic. Otherwise sort by a stable key such as code, then subject id, then message. Say which one you chose and why.
3. Add a test: generate one seed and intent in subprocesses at PYTHONHASHSEED 0 and 1, and assert byte-identical assembly_report.json and validation_report.json. Positive control: the test fails on main.
4. STOP and report if `world.yaml`, the provenance manifest or any assembled world content changes. This ticket changes only report ordering.

## Out of Scope
- WorldProceduralGenerator, fixed by its own ticket.
- The warnings' content and count.
- Any other set-order site.

## Acceptance Criteria
1. Both reports are byte-identical across PYTHONHASHSEED 0 and 1 for seeds 42, 7 and 12345 (timestamps normalised the same way as the generator ticket's check).
2. The new test fails on main and passes on the fix. Both results are shown.
3. world.yaml and the provenance manifest are unchanged, main vs fix, shown by digest.
4. Scoped tests pass, capped: tests/unit/worldgeneration, the worldassembly integration tests that read ProceduralCompositionGenerator, and generate_registry plus the paths guard.
5. The parity or divergence record is updated if one claims report determinism. Check SUBSTRATE-NEW-002 and the world-assembly contract docs.

## Related Tickets
- TCK-20261030-WORLD-GENERATOR-RESOURCE-TYPE-PICK-FOLLOWS-PYTHONHASHSEED (found it; divergence 2.145)
- TCK-20261029-STATE-SET-ORDER-FOLLOWS-PYTHONHASHSEED (#795, the set-order audit)

## Related Docs
- docs/world/generator_contract.md
- docs/guidelines/intentional_divergences.md §2.145

## Related Stored Artifacts
- The generator ticket's stored_artifacts (investigation.md) once it lands.

## Related Code Areas
- src/worldgeneration/generator.py (ProceduralCompositionGenerator)
- src/worldassembly/ (report writers)

## Assumptions / Open Questions
- Hotfix if the fix is a sort at one site. Standard if the order needs a design choice across several producers.

## Implementation Notes

## Test Summary

## Files Changed

## Completion Summary
