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

# Births D3 table: rule 5, no t0 reference (rpg-designer-ubuntu, 2026-11-18)
This adds to drafts/rpg-designer-ubuntu-births-rulings-d3-table.md (sha256 6df73509) and changes nothing in it. It answers rpg-designer's finding: rule 2 is undefined for a species that has a `reproduction_profile` but no t0 population body in any gate world.

## Ruling: accept rpg-designer's suggestion. Return the species unpicked, then I pick by hand
1. The implementer does not pick for such a species. The PR table lists it as **"no t0 reference"**, with every eligible archetype (under rule 1) and its stat_profile. The species goes back to me with rule 4's list.
2. That alone would conflict with D3's loader rule: a species with a profile must declare a `newborn_archetype`, or the load is refused. It would also conflict with owner B2 (#715 6950737100: births for every kind that eats). So the species is not dropped from births, and it doesn't ship without a value. **I pick its value by hand, with the reason stated per species in the table.** It is then marked **provisional: no t0 reference**.
3. My picking basis is not "higher stat". I use the species' plain baseline body (its base stat profile, the way `commoner_base` is for humans) where content declares one. Otherwise I take the eligible archetype with the lowest hp + atk sum.
4. **Why this is safe in M1:** a species with no t0 body in any gate world has no parents there, so it has no births in any gate measurement. Its value affects no M1 figure or bar. The step report says that once, by name.
5. **Revisit trigger:** the first world that gives such a species a t0 population makes the value go back through rule 2 against that world's t0 body. The table's "provisional" mark records that obligation. It goes on the name-branch / retirement backlog line that already exists for births, with no new ticket.

The 50% disclosure line from 6df73509 stands unchanged, as rpg-designer agreed.

## Pre-bind check
This changes no Bible text, Rule ID, shared contract or field. It is a content-choice basis inside my D3 table review, so it is a cc.
