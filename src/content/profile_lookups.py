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
        return self.need_profiles.get(def_id)

    def get_risen_profile(self, def_id: str) -> Optional[RisenProfileDefinition]:
        """The risen profile with this ID, or None."""
        return self.risen_profiles.get(def_id)

    def get_reproduction_profile(self, def_id: str) -> Optional[ReproductionProfileDefinition]:
        """The reproduction profile with this id, or None."""
        return self.reproduction_profiles.get(def_id)

    def get_sense_profile(self, def_id: str) -> Optional[SenseProfileDefinition]:
        return self.sense_profiles.get(def_id)

    def get_drive_profile(self, def_id: str) -> Optional[DriveProfileDefinition]:
        return self.drive_profiles.get(def_id)

    def get_cognition_profile(self, def_id: str) -> Optional[CognitionProfileDefinition]:
        return self.cognition_profiles.get(def_id)

    def get_stats_profile(self, def_id: str) -> Optional[StatsProfileDefinition]:
        return self.stats_profiles.get(def_id)

    def get_combat_profile(self, def_id: str) -> Optional[CombatProfileDefinition]:
        return self.combat_profiles.get(def_id)

    def get_inventory_profile(self, def_id: str) -> Optional[InventoryProfileDefinition]:
        return self.inventory_profiles.get(def_id)

    def get_skill_profile(self, def_id: str) -> Optional[SkillProfileDefinition]:
        return self.skill_profiles.get(def_id)
