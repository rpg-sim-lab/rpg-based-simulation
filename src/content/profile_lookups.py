"""The by-id getters of the profile families (need, risen, reproduction, sense, drive, cognition, stats, combat, inventory, skill), moved verbatim out of `CatalogRepository`
(code-health class-length ceiling; TCK-20261109-M1-BASIC-WILD-BIRTHS-FOR-EVERY-LIVING-KIND). `CatalogRepository` inherits them and still owns and fills the index dicts."""
from __future__ import annotations

from typing import Dict, Optional

from src.content.schema import (
    CognitionProfileDefinition,
    CombatProfileDefinition,
    DriveProfileDefinition,
    InventoryProfileDefinition,
    NeedProfileDefinition,
    ReproductionProfileDefinition,
    RisenProfileDefinition,
    SenseProfileDefinition,
    SkillProfileDefinition,
    StatsProfileDefinition,
)


class ProfileLookups:
    """The by-id profile getters; the index dicts they read are declared here and owned and filled by `CatalogRepository`."""

    need_profiles: Dict[str, NeedProfileDefinition]
    risen_profiles: Dict[str, RisenProfileDefinition]
    reproduction_profiles: Dict[str, ReproductionProfileDefinition]
    sense_profiles: Dict[str, SenseProfileDefinition]
    drive_profiles: Dict[str, DriveProfileDefinition]
    cognition_profiles: Dict[str, CognitionProfileDefinition]
    stats_profiles: Dict[str, StatsProfileDefinition]
    combat_profiles: Dict[str, CombatProfileDefinition]
    inventory_profiles: Dict[str, InventoryProfileDefinition]
    skill_profiles: Dict[str, SkillProfileDefinition]

    def get_need_profile(self, def_id: str) -> Optional[NeedProfileDefinition]:
        """The need profile with this id, or None."""
        return self.need_profiles.get(def_id)

    def get_risen_profile(self, def_id: str) -> Optional[RisenProfileDefinition]:
        """The risen profile with this ID, or None."""
        return self.risen_profiles.get(def_id)

    def get_reproduction_profile(self, def_id: str) -> Optional[ReproductionProfileDefinition]:
        """The reproduction profile with this id, or None."""
        return self.reproduction_profiles.get(def_id)

    def get_sense_profile(self, def_id: str) -> Optional[SenseProfileDefinition]:
        """The sense profile with this id, or None."""
        return self.sense_profiles.get(def_id)

    def get_drive_profile(self, def_id: str) -> Optional[DriveProfileDefinition]:
        """The drive profile with this id, or None."""
        return self.drive_profiles.get(def_id)

    def get_cognition_profile(self, def_id: str) -> Optional[CognitionProfileDefinition]:
        """The cognition profile with this id, or None."""
        return self.cognition_profiles.get(def_id)

    def get_stats_profile(self, def_id: str) -> Optional[StatsProfileDefinition]:
        """The stats profile with this id, or None."""
        return self.stats_profiles.get(def_id)

    def get_combat_profile(self, def_id: str) -> Optional[CombatProfileDefinition]:
        """The combat profile with this id, or None."""
        return self.combat_profiles.get(def_id)

    def get_inventory_profile(self, def_id: str) -> Optional[InventoryProfileDefinition]:
        """The inventory profile with this id, or None."""
        return self.inventory_profiles.get(def_id)

    def get_skill_profile(self, def_id: str) -> Optional[SkillProfileDefinition]:
        """The skill profile with this id, or None."""
        return self.skill_profiles.get(def_id)
