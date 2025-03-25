from dataclasses import dataclass, field
from typing import Dict

from models.enums import LocationRarityType
from models.config import LocationLevel

@dataclass
class Location:
    rarity: LocationRarityType
    min_character_level: int
    levels: Dict[int, LocationLevel]
    keys: int
    available: bool = True
    current_level: int = 0
    cooldown_until: int = 0
    
    def get_upgrade_cost(self) -> int:
        return self.levels.get(self.current_level + 1, LocationLevel(0, 0)).cost
    
    def get_upgrade_xp_reward(self) -> int:
        return self.levels.get(self.current_level + 1, LocationLevel(0, 0)).xp_reward
    
    def get_upgrade_keys_reward(self) -> int:
        return self.keys if self.is_last_upgrade() else 0
    
    def is_last_upgrade(self) -> bool:
        return max(self.levels.keys()) == self.current_level + 1 