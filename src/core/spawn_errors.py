"""Spawn-placement errors, moved verbatim out of src/systems/world_systems/generator.py (which re-exports the name) so the engine can catch it without importing the systems layer."""
from __future__ import annotations


class NoFreeSpawnTileError(RuntimeError):
    """`free_spawn_position` found no clear tile in its search radius (births record the newborn as unplaced; a bare RuntimeError from anywhere else is a bug)."""
