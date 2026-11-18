---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261119-THE-SPECIES-MIRROR-IS-GONE-KIND-IS-THE-ONLY-SPECIES-FIELD
artifact_type: plan
tags: []
---

# Plan
1. Remove the three mirror writers; move every reader to `species_of()`; delete `get_species_id_str`.
2. `profile_id_for`: explicit `need_profile_id`, else the species' catalog `need_profile`, else DEBUG + None (base rates); `unprofiled_need_counts` for the bar.
3. K12 AST test: no `"species_id"` key sites in `src` except the `event_shapers` payload field.
4. Test fixtures: owner-approved patch f55b8167 (readers to `species_of`, builders `.kind(<species>)`, 8 assertion changes).
5. Extract `_population_properties_and_species` from `WorldCompiler.compile` to keep both length rows under their ceilings.
6. Measure: K11 projection plus the unprofiled-needs probe at s42 x 5000, 3 gate worlds.
