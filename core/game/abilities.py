from abc import ABC, abstractmethod
import random

class Ability(ABC):
    @abstractmethod
    def use(self, user, target) -> str:
        raise NotImplementedError

class Fireball(Ability):
    def __init__(self, damage: int):
        self.damage = int(damage)
    def use(self, user, target) -> str:
        actual = max(0, self.damage - target.armor)
        target.health -= actual
        return f"{user.name} casts Fireball at {target.name} for {actual} dmg"

class Heal(Ability):
    def __init__(self, amount: int):
        self.amount = int(amount)
    def use(self, user, target) -> str:
        target.health += self.amount
        return f"{user.name} heals {target.name} for {self.amount} HP"

class Shield(Ability):
    def __init__(self, bonus: int, duration: int = 1):
        self.bonus = int(bonus)
        self.duration = int(duration)
    def use(self, user, target) -> str:
        if not hasattr(target, "_temp_armor"): target._temp_armor = 0
        target._temp_armor += self.bonus
        target._temp_armor_turns = max(getattr(target, "_temp_armor_turns", 0), self.duration)
        return f"{user.name} shields {target.name} (+{self.bonus} armor) for {self.duration} turns"

class Freeze(Ability):
    def __init__(self, duration: int = 1):
        self.duration = int(duration)
    def use(self, user, target) -> str:
        target._frozen_turns = max(getattr(target, "_frozen_turns", 0), self.duration)
        return f"{user.name} freezes {target.name} for {self.duration} turns!"

class Doom(Ability):
    def __init__(self, delay: int = 3):
        self.delay = int(delay)
    def use(self, user, target) -> str:
        target._doom_counter = self.delay
        return f"{user.name} casts Doom on {target.name}. Death in {self.delay} turns.."

class Thunderstorm(Ability):
    def __init__(self, dmg_min=20, dmg_max=40, hits_min=1, hits_max=4):
        self.dmg_min, self.dmg_max = dmg_min, dmg_max
        self.hits_min, self.hits_max = hits_min, hits_max
    def use(self, user, target) -> str:
        hits = random.randint(self.hits_min, self.hits_max)
        total_dmg = 0
        logs = []
        for _ in range(hits):
            raw = random.randint(self.dmg_min, self.dmg_max)
            actual = max(0, raw - target.armor)
            target.health -= actual
            total_dmg += actual
            logs.append(str(actual))
        return f"{user.name} summons Thunderstorm! Hits: {hits} ({', '.join(logs)}). Total: {total_dmg} dmg"

class BrainSap(Ability):
    def __init__(self, damage=60, cooldown=5):
        self.damage = damage
        self.cooldown = cooldown
    def use(self, user, target) -> str:
        last_turn = getattr(user, "_brain_sap_last", -999)
        current_turn = getattr(user, "_current_turn_counter", 0)
        
        if (current_turn - last_turn) < self.cooldown:
            rem = self.cooldown - (current_turn - last_turn)
            return f"{user.name} fails BrainSap (Cooldown: {rem} turns)"
        
        actual = max(0, self.damage - target.armor)
        target.health -= actual
        user._brain_sap_last = current_turn
        return f"{user.name} drains mind of {target.name} for {actual} dmg"

class DarkBlast(Ability):
    def __init__(self, damage=80, min_turn=3):
        self.damage = damage
        self.min_turn = int(min_turn)
    
    def use(self, user, target) -> str:
        current_turn = getattr(user, "_current_turn_counter", 0) + 1
        
        if current_turn < self.min_turn:
            return f"{user.name} fails DarkBlast (Available from turn {self.min_turn})"
        
        actual = max(0, self.damage - target.armor)
        target.health -= actual
        return f"{user.name} blasts {target.name} with Darkness for {actual} dmg!"

class BlackHole(Ability):
    def __init__(self, damage=50, min_turn=4):
        self.name = "Black Hole"
        self.damage = damage
        self.description = "Creates a singularity.." 
    
    def use(self, user, target) -> str:
        current_turn = getattr(user, "_current_turn_counter", 0) + 1
        
        if current_turn < self.min_turn:
            return f"{user.name} fails BlackHole (Available from turn {self.min_turn})"
        
        actual = max(0, self.damage - target.armor)
        target.health -= actual
        target._frozen_turns += 1
        
        return f"{user.name} summons BlackHole, dealing {actual} dmg and Freezing {target.name} for 1 turn!"