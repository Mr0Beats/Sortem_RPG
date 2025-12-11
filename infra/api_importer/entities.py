import random
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Any

@dataclass
class Item:
    id: int | str = 0
    name: str = "Unknown Item"
    slot: Optional[str] = None
    bonus_hp: int = 0
    bonus_armor: int = 0
    bonus_attack: int = 0
    stat_modifiers: Dict[str, float | int] = field(default_factory=dict)

@dataclass
class Skill:
    id: int | str = 0
    name: str = "Unknown Skill"
    description: str = ""
    power: Optional[float] = None
    cooldown: Optional[float] = None
    
    def __repr__(self):
        return self.name

    def use(self, user: 'Character', target: 'Character') -> str:
        multiplier = self.power if self.power is not None else 1.5
        atk = user.attack
        raw_damage = int(atk * multiplier)
        
        actual_dmg = target.take_damage(raw_damage)
        
        return f"{user.name} casts '{self.name}' on {target.name}! (Dmg: {actual_dmg})"

@dataclass
class Character:
    id: int | str
    name: str
    game: str
    level: int
    stats: Dict[str, float | int | None] = field(default_factory=dict)
    skills: List[Skill] = field(default_factory=list)
    equipment: List[Item] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    _temp_armor: int = field(init=False, default=0)
    _frozen_turns: int = field(init=False, default=0)
    _doom_counter: Optional[int] = field(init=False, default=None)

    def __post_init__(self):
        self._temp_armor = 0
        self._frozen_turns = 0
        self._doom_counter = None
        if self.stats is None: self.stats = {}

    @property
    def items(self) -> List[Item]:
        return self.equipment
    
    @items.setter
    def items(self, value: List[Item]):
        self.equipment = value

    @property
    def abilities(self) -> List[Skill]:
        return self.skills
    
    @abilities.setter
    def abilities(self, value: List[Skill]):
        self.skills = value

    @property
    def health(self) -> int:
        val = self.stats.get("health")
        if val is None: val = self.stats.get("max_hp", 100)
        return int(val)

    @health.setter
    def health(self, value: int):
        self.stats["health"] = value

    @property
    def max_hp(self) -> int:
        return int(self.stats.get("max_hp", 100))
    
    @property
    def base_hp(self) -> int: return self.max_hp

    @property
    def attack(self) -> int:
        base = self.stats.get("attack") or self.stats.get("base_attack", 10)
        item_bonus = sum(i.bonus_attack for i in self.equipment if hasattr(i, 'bonus_attack'))
        return int(base) + item_bonus
    
    @property
    def base_attack(self) -> int: return int(self.stats.get("attack", 10))

    @property
    def critical_chance(self) -> float:
        return self.stats.get("crit_chance", 0.1)

    @property
    def critical_multiplier(self) -> float:
        return self.stats.get("crit_multiplier", 1.5)

    @property
    def armor(self) -> int:
        base = int(self.stats.get("defense", self.stats.get("armor", 0)))
        item_bonus = sum(i.bonus_armor for i in self.equipment if hasattr(i, 'bonus_armor'))
        return base + item_bonus + self._temp_armor

    @property
    def base_armor(self) -> int: return int(self.stats.get("defense", 0))

    def is_alive(self) -> bool:
        return self.health > 0

    def take_damage(self, raw_amount: int) -> int:
        reduction = self.armor
        final_damage = max(1, raw_amount - reduction)
        self.health = max(0, self.health - final_damage)
        return final_damage

    def attack_target(self, target: 'Character') -> str:
        if self._frozen_turns > 0:
            return f"{self.name} is frozen and cannot attack"

        base_dmg = self.attack
        is_crit = random.random() < self.critical_chance
        
        crit_text = ""
        if is_crit:
            base_dmg = int(base_dmg * self.critical_multiplier)
            crit_text = " (CRIT!)"

        dealt = target.take_damage(base_dmg)
        
        return f"{self.name} hits {target.name}{crit_text} for {dealt} damage!"

    def end_turn_update(self) -> List[str]:
        logs = []
        if self._temp_armor > 0:
            self._temp_armor = 0
            
        if self._frozen_turns > 0:
            self._frozen_turns -= 1
            if self._frozen_turns == 0:
                logs.append(f"{self.name} thawed out")
            else:
                logs.append(f"{self.name} is frozen")

        if self._doom_counter is not None:
            self._doom_counter -= 1
            if self._doom_counter <= 0 and self.is_alive():
                self.health = 0
                self._doom_counter = None
                logs.append(f"☠️ DOOM claims {self.name}!")
                
        return logs

    def equip(self, item: Item):
        self.equipment.append(item)
        if hasattr(item, 'bonus_hp') and item.bonus_hp:
            self.health += item.bonus_hp