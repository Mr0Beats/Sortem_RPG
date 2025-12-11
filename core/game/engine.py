import random
from typing import List, Generator, Optional, Tuple

from infra.api_importer.entities import Character, Skill
from core.game.grouping import IGroupingStrategy

class GameEngine:
    def __init__(self):
        self.characters: List[Character] = []

    def add_character(self, char: Character):
        self.characters.append(char)

    def get_character_by_name(self, name: str) -> Optional[Character]:
        return next((c for c in self.characters if c.name.lower() == name.lower()), None)

    def battle_simulation_step(self, 
                               characters: List[Character], 
                               grouping_strategy: IGroupingStrategy) -> Generator[str, None, None]:
        
        group1, group2 = grouping_strategy.group(characters)

        if not group1 or not group2:
             yield "Grouping failed: Not enough characters for this strategy"
             return

        all_participants = group1 + group2
        random.shuffle(all_participants)

        for actor in all_participants:
            if not actor.is_alive(): continue
            
            enemies = group2 if actor in group1 else group1
            alive_enemies = [e for e in enemies if e.is_alive()]
            
            if not alive_enemies:
                 return

            if actor._frozen_turns > 0:
                 yield f" > ❄️ {actor.name} is frozen and skips turn!"
                 for log in actor.end_turn_update():
                      yield f"[STATUS] {log}"
                 continue

            used_actions = 0
            max_uses = 1

            if actor.abilities and random.random() < 0.3: 
                 target = random.choice(alive_enemies) 
                 ab = random.choice(actor.abilities)
                 
                 full_log_msg = ab.use(actor, target)
                 yield f" > (Skill) {full_log_msg}"
                 used_actions += 1
            
            if used_actions == 0 and alive_enemies:
                 target = random.choice(alive_enemies)
                 attack_log_msg = actor.attack_target(target)
                 yield f" > (Attack) {attack_log_msg}"
            
            logs = actor.end_turn_update()
            for log in logs:
                 yield f"[STATUS] {log}"