---
status: active
layer: engine
authority: P1
audience: developer
---

# Local Environment & World-Interaction Contract

This document defines the authoritative semantics for environment and building interactions in the `src` engine.

## 1. Terrain & Spatial Constraints
### 1.1 Blocked Movement (WALL)
- Any tile marked as `WALL` in the `AuthoritativeState.terrain` map is impassable.
- Movement attempts into a `WALL` tile are rejected with `PATH_NOT_FOUND`.

### 1.2 Combat Obstruction (Line of Sight)
- `WALL` tiles and `Buildings` obstruct Line of Sight (LoS).
- Attacks through an obstructed tile are rejected with `LOS_OBSTRUCTED`.
- LoS is calculated via a Manhattan-step path check between attacker and target.

## 2. Building Interaction Semantics
### 2.1 Occupancy & Obstruction
- Functional buildings act as solid obstacles for movement and combat LoS.
- Rejection reason: `BUILDING_OBSTRUCTION`.
- **Lodging (F3, divergence 2.155).** A subject served a bed at a building lodges inside it: while it lodges it stands on no tile (`navigation.lodged_in` is the building id, `position` is the building's own tile), so it holds no tile beside the building, and, as the building is a solid obstacle, no one outside can reach or see it, and it sees no one outside. It is in no occupancy map or spatial index, is not a legal attack target or splash target, witnesses nothing and is not a swap partner; the lodgers of one building share its tile, which is no occupant's tile. A building lodges at most its content `beds`; the lodger count is derived from `lodged_in`, never stored on the building. `lodged_in` is set and cleared only by the apply path.

### 2.2 Building Services (REST)
- Entities located at a building tile of type `inn` or `home` can issue a `REST` intent.
- **REST Bonus**: 5x Passive Healing multiplier + 10.0 Readiness boost per tick.
- Sabotaged buildings (Functional: False) do not provide services.

## 3. Position-Sensitive Tactical Behavior
### 3.1 High Ground Bonus
- Attacker on a `HILL` terrain receives a damage bonus (+5).

### 3.2 Bracketing (Flanking)
- A target is **Bracketed** if it is adjacent to at least two hostiles on opposite sides (e.g., North and South, or East and West).
- Attackers receive a bracketing bonus (+3) when attacking a bracketed target.

## 4. Known Exclusions
- **Dynamic Terrain**: Terrain cannot currently be modified during a simulation (Except for buildings via sabotage).
- **Complex LoS**: Sophisticated raycasting is deferred; Manhattan-step is the current authoritative law.
- **Atmospheric Effects**: Fog/Night effects are currently out of scope.
