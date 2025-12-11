import random
from .models import Character
from . import abilities

class CharGenerator:
    NAMES = [
        "Thorin", "Azog", "Gandalf", "Saruman", 
        "Legolas", "Gimli", "Aragorn", "Boromir",
        "Lurtz", "Gollum", "Frodo", "Sam"
    ]

    ABILITY_POOL = [
        lambda: abilities.Fireball(random.randint(20, 40)),
        lambda: abilities.Heal(random.randint(15, 30)),
        lambda: abilities.Shield(random.randint(3, 6), random.randint(1, 3)),
        lambda: abilities.Freeze(random.randint(1, 2)),
        lambda: abilities.Doom(random.randint(2, 4)),
        lambda: abilities.Thunderstorm(5, 15, 1, 3),
        lambda: abilities.BrainSap(50, 4),
        lambda: abilities.DarkBlast(60, 2),
        lambda: abilities.BlackHole(random.randint(40, 60), random.randint(3, 5)) 
    ]

    @staticmethod
    def create_random_char() -> Character:
        name = random.choice(CharGenerator.NAMES)
        unique_name = f"{name}_{random.randint(10, 99)}"
        
        hp = random.randint(80, 150)
        armor = random.randint(0, 8)
        atk = random.randint(8, 18)
        
        char = Character(unique_name, hp, armor, atk)
        
        
        max_possible = len(CharGenerator.ABILITY_POOL)
        num_abilities = random.randint(1, min(3, max_possible)) 
        
        unique_ability_factories = random.sample(CharGenerator.ABILITY_POOL, num_abilities)
        
        for ability_factory in unique_ability_factories:
            char.abilities.append(ability_factory())
            
        return char

    @staticmethod
    def generate_team(size: int = 4) -> list[Character]:
        return [CharGenerator.create_random_char() for _ in range(size)]