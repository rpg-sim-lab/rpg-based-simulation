---
status: active
layer: core
authority: P2
audience: agent
ticket_id: TCK-20261119-THE-SPECIES-MIRROR-IS-GONE-KIND-IS-THE-ONLY-SPECIES-FIELD
artifact_type: investigation
tags: []
---

# Investigation
57 test files read or wrote the dead mirror; 46 failed after the src change (45 test files plus a helper). Shapes: readers `(e.identity.properties or {}).get("species_id")` (to `species_of(e)`); builders with a role-word kind plus a mirror write (to `.kind(<species>)`); test premises that depended on the mirror (presenter no-species, common_knowledge no-species hostile, occupation_field K6/K7) ruled by rpg-designer. The throwaway-copy proof (archive of 7549105d7 plus the patch) turned 45 of 45 failing files green; the owner approved the patch (#715 6985677098 / 6985692443). Statics and the 93-file regression ran on 23d6bf642.
