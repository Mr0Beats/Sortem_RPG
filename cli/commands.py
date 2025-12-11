from infra.io import IDisplay
from core.game.engine import GameEngine
from core.game.models import Character, Item
from core.game import abilities
from core.game.generator import CharGenerator
from core.game.grouping import IGroupingStrategy, SplitInTwoStrategy, OneVsAllStrategy
from core.text.document import Document, Heading, Paragraph
from .presenter import Presenter
from typing import Optional, Dict, List, Any, Tuple
from abc import ABC, abstractmethod
import random

from core.game.mapper import map_imported_character_to_core
from infra.api_importer.importer_service import import_character
from infra.persistence import PersistenceService
from core.game.gamestate import GameSession
from infra.storage import GameStorage

class OneVsBossStrategy(IGroupingStrategy):
    def __init__(self):
        self.boss = Character(
            id="boss_world_eater",
            name="Evil Boss", 
            game="custom",
            level=99,
            stats={
                "max_hp": 250000,
                "health": 250000,
                "attack": 250, 
                "defense": 100,
                "crit_chance": 0.2,
                "crit_multiplier": 2.0
            }
        )

    def group(self, characters: List[Character]) -> Tuple[List[Character], List[Character]]:
        return characters, [self.boss]

class SplitInTwoStrategy(IGroupingStrategy):
    def group(self, characters: List[Character]) -> Tuple[List[Character], List[Character]]:
        mid = len(characters) // 2
        return characters[:mid], characters[mid:]

class OneVsAllStrategy(IGroupingStrategy):
    def group(self, characters: List[Character]) -> Tuple[List[Character], List[Character]]:
        if not characters: return [], []
        return characters[:-1], [characters[-1]]

class TwoVsTwoStrategy(IGroupingStrategy):
    def group(self, characters: List[Character]) -> Tuple[List[Character], List[Character]]:
        if len(characters) < 4: return [], []
        return characters[:2], characters[2:4]

class FiveVsFiveStrategy(IGroupingStrategy):
    def group(self, characters: List[Character]) -> Tuple[List[Character], List[Character]]:
        if len(characters) < 10: return [], []
        return characters[:5], characters[5:10]

class Command(ABC):
    @abstractmethod
    def execute(self, args: list): raise NotImplementedError

class GameCommand(Command):
    def __init__(self, engine: GameEngine, display: IDisplay):
        self.engine, self.display = engine, display
        
    def _parse_args(self, args: list) -> Dict[str, Any]:
        return {"raw_args": args}
        
    def _validate(self, parsed_args: dict) -> Optional[str]:
        return None 

    @abstractmethod
    def _do_execute(self, parsed_args: dict):
        raise NotImplementedError

    def execute(self, args: list):
        try:
            parsed_args = self._parse_args(args)
            validation_error = self._validate(parsed_args)
            
            if validation_error:
                self.display.show(validation_error)
                return
            
            self._do_execute(parsed_args)
            
        except Exception as e:
            self.display.show(f"Command execution error: {e}")

class SaveAllCommand(GameCommand):
    def _do_execute(self, parsed_args: dict):
        if not self.engine.characters:
            self.display.show("Nothing to save (character list is empty)")
            return

        if PersistenceService.save_characters(self.engine.characters):
            self.display.show(f"Successfully saved {len(self.engine.characters)} characters to disk")
        else:
            self.display.show("Error saving characters")

class LoadAllCommand(GameCommand):
    def _do_execute(self, parsed_args: dict):
        self.display.show("Loading save file..")
        loaded_chars = PersistenceService.load_characters()
        if loaded_chars:
            for char in loaded_chars:
                if hasattr(char, 'reload_image'): 
                    char.reload_image()
                elif hasattr(char, 'image_path'):
                    pass

            self.engine.characters = loaded_chars 
            self.display.show(f"Successfully loaded {len(loaded_chars)} characters")

            names = [c.name for c in loaded_chars]
            self.display.show(f"   Roster: {', '.join(names)}")
        else:
            self.display.show("Save file not found or empty")

class ImportCharCommand:
    def __init__(self, game_engine, display):
        self.game_engine = game_engine
        self.display = display

    def execute(self, args):
        if isinstance(args, list):
            parts = args
        else:
            parts = args.split()
        
        if not parts:
            self.display.show("Usage: import <source> <name> [level]")
            return

        if len(parts) < 2:
            self.display.show("Error: Missing arguments")
            self.display.show("Usage: import genshin <Name> [level]")
            self.display.show("Example: import genshin Xiao 90")
            return

        source = parts[0].lower()
        char_name = parts[1]
        
        level = 90
        if len(parts) > 2:
            try:
                level = int(parts[2])
            except ValueError:
                self.display.show("Level must be a number. Defaulting to 90")

        self.display.show(f"Connecting to {source} API to fetch '{char_name}'..")

        try:
            character = import_character(source, name=char_name, level=level)
            
            self.game_engine.add_character(character)
            
            self.display.show(f"Success! Imported: {character.name} (Lvl {character.level})")
            self.display.show(f"Stats: {character.stats}")
            if character.metadata.get('ui_assets'):
                 self.display.show(f"Icon: {character.metadata['ui_assets']['icon_url']}")
            
        except ValueError as ve:
            self.display.show(f"Validation Error: {ve}")
        except Exception as e:
            self.display.show(f"Network/Parsing Error: {e}")

class ListCharsCommand(GameCommand):
    def _do_execute(self, parsed_args: dict):
        if not self.engine.characters:
            self.display.show("No characters")
            return
        
        self.display.show("= Available Characters =")
        
        for c in self.engine.characters:
            self.display.show(Presenter.char_row(c))
            
            if c.items:
                self.display.show(f"  > Items: {[i.name for i in c.items]}")
            if c.abilities:
                skills_list = [getattr(a, 'name', type(a).__name__) for a in c.abilities]
                self.display.show(f"  > Abilities: {skills_list}")

class AddItemCommand(GameCommand):
    def _do_execute(self, parsed_args: dict):
        char_name = self.display.prompt("Character Name to equip item: ")
        char: Optional[Character] = next((c for c in self.engine.characters if c.name == char_name), None)
        if not char:
            return self.display.show("Character not found")

        name = self.display.prompt("Item Name: ")
        try:
            hp = int(self.display.prompt("Bonus HP (0): ") or 0)
            arm = int(self.display.prompt("Bonus Armor (0): ") or 0)
            atk = int(self.display.prompt("Bonus Attack (0): ") or 0)
            
            new_item = Item(name, hp=hp, armor=arm, atk=atk)
            char.equip(new_item)
            self.display.show(f"Equipped {name} to {char.name}. Stats updated")
        except ValueError:
            self.display.show("Invalid number format")

class AddAbilityCommand(GameCommand):
    def __init__(self, engine: GameEngine, display: IDisplay):
        super().__init__(engine, display)
        self.map = {
            "fireball": lambda: abilities.Fireball(30),
            "heal": lambda: abilities.Heal(20),
            "shield": lambda: abilities.Shield(4, 2),
            "freeze": lambda: abilities.Freeze(1),
            "doom": lambda: abilities.Doom(3),
            "storm": lambda: abilities.Thunderstorm(5, 15),
            "brainsap": lambda: abilities.BrainSap(60, 5),
            "darkblast": lambda: abilities.DarkBlast(80, 3),
            "blackhole": lambda: abilities.BlackHole(50, 4)
        }
        
    def _do_execute(self, parsed_args: dict):
        char_name = self.display.prompt("Character Name: ")
        char: Optional[Character] = next((c for c in self.engine.characters if c.name == char_name), None)
        if not char:
            return self.display.show("Character not found")
        
        ab_name = self.display.prompt(f"Ability ({', '.join(self.map.keys())}): ").lower()
        
        if ab_name in self.map:
            new_ability = self.map[ab_name]()
            char.abilities.append(new_ability)
            self.display.show(f"Added {type(new_ability).__name__} to {char.name}")
        else:
            self.display.show("Unknown ability")

class UseAbilityCommand(GameCommand):
    def _parse_args(self, args: list) -> dict:
        return {"char_name": args[0] if args else None}
    
    def _validate(self, params: dict) -> Optional[str]:
        if not params["char_name"]:
            return "Error: Character name is required"
        return None

    def _do_execute(self, params: dict):
        char = self.engine.get_character_by_name(params["char_name"])
        
        if not char:
            self.display.show(f"Character '{params['char_name']}' not found")
            return

        external_skills = char.metadata.get("imported_skills")
        
        if not external_skills:
            self.display.show(f"{char.name} has no imported Genshin abilities or metadata")
            return

        self.display.show("Available Skills:")
        for i, (name, _) in enumerate(external_skills):
            self.display.show(f" {i + 1}. {name}")
            
        try:
            skill_index_str = self.display.prompt("Enter skill number (1, 2, or 3): ")
            skill_index = int(skill_index_str) - 1
            
            if skill_index < 0 or skill_index >= len(external_skills):
                self.display.show("Invalid skill number")
                return
        except ValueError:
            self.display.show("Invalid input. Please enter a number")
            return

        skill_name, skill_description = external_skills[skill_index] 
        
        self.display.show(f"- {char.name} uses their ability! -")
        self.display.show(f"Ability: **{skill_name}**")
        
        if "Elemental Skill" in skill_name:
            bonus_armor = int(char.base_armor * 0.5) 
            char._temp_armor += bonus_armor
            char._temp_armor_turns = 2
            self.display.show(f"Effect: {char.name} forms a shield, gaining **+{bonus_armor} Armor** for 2 turns!")
        
        elif "Elemental Burst" in skill_name:
            target_name = self.display.prompt("Target Character Name: ")
            target = self.engine.get_character_by_name(target_name)
            
            if not target or target.name == char.name or not target.is_alive():
                self.display.show("Invalid, self-targeting, or dead target. Burst effect failed")
                return

            base_dmg_factor = 2 
            damage_to_deal = int(char.base_attack * base_dmg_factor) 
            
            damage_dealt = max(0, damage_to_deal - target.armor)
            target.health -= damage_dealt
            
            self.display.show(f"Effect: {char.name} unleashes an ultimate **Elemental Burst** targeting {target.name}!")
            self.display.show(f"**Dealt {damage_dealt} damage** (Target HP remaining: {target.health})")

        else:
            self.display.show(f"Effect: {skill_name} is used (No game effect applied)")

class ShowMetadataCommand(GameCommand):
    def _parse_args(self, args: list) -> dict:
        return {"char_name": args[0] if args else None}

    def _validate(self, params: dict) -> Optional[str]:
        if not params["char_name"]:
            return "Error: Character name is required"
        return None

    def _do_execute(self, params: dict):
        char = self.engine.get_character_by_name(params["char_name"])
        
        if not char:
            self.display.show(f"Character '{params['char_name']}' not found")
            return

        meta = char.metadata
        
        if not meta:
            self.display.show(f"{char.name} has no external metadata")
            return
            
        self.display.show(f"=== Metadata for {char.name} ===")
        self.display.show(f"Source Game: {meta.get('game_source', 'N/A').upper()}")
        self.display.show(f"Element (Vision): **{meta.get('element', 'N/A')}**")
        self.display.show(f"Weapon Type: {meta.get('weapon_type', 'N/A')}")
        self.display.show(f"Description: {meta.get('description', 'N/A')[:60]}...")

        self.display.show("- Imported Skills -")
        imported_skills = meta.get("imported_skills", [])
        if imported_skills:
            for i, (name, desc) in enumerate(imported_skills):
                self.display.show(f" {i+1}. {name}")
                self.display.show(f"       Description: {desc[:80]}.")
        else:
            self.display.show("No skills found")

class StartGameCommand(GameCommand):
    def _do_execute(self, parsed_args: dict):
        if not self.engine.characters:
            self.display.show("Cannot start game: No characters available. Use 'create' or 'import'")
            return

        session = GameSession(self.engine, self.display)
        session.run()
        self.display.show("Returned to Main Menu")

class BattleCommand(GameCommand):
    def __init__(self, engine: GameEngine, display: IDisplay):
        super().__init__(engine, display)
        self.strategies: Dict[str, IGroupingStrategy] = {
            "split": SplitInTwoStrategy(),
            "1vsall": OneVsAllStrategy(),
            "2vs2": TwoVsTwoStrategy(),
            "5vs5": FiveVsFiveStrategy(),
            "vsboss": OneVsBossStrategy(),
        }

    def _parse_args(self, args: list) -> dict:
        if args and args[0].lower() in self.strategies:
            return {"strategy_name": args[0].lower()}
        
        self.display.show("\n-- Select Battle Mode --")
        modes_list = list(self.strategies.keys())
        
        for index, mode in enumerate(modes_list, 1):
            self.display.show(f"[{index}] {mode}")
            
        while True:
            choice = self.display.prompt("Enter mode number: ").strip()
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(modes_list):
                    selected_mode = modes_list[idx]
                    return {"strategy_name": selected_mode}
            
            self.display.show("Invalid choice. Please enter a valid number")

    def _validate(self, params: dict) -> Optional[str]:
        strategy_name = params["strategy_name"]
        
        if strategy_name not in self.strategies:
            return f"Unknown strategy: {strategy_name}"
        
        min_chars = 1
        if strategy_name == "2vs2": min_chars = 4
        elif strategy_name == "5vs5": min_chars = 10
        
        if len(self.engine.characters) < min_chars:
            return f"Not enough characters for {strategy_name.upper()} mode. Requires {min_chars} loaded characters (you have {len(self.engine.characters)})"
            
        return None

    def _do_execute(self, params: dict):
        strategy_name = params["strategy_name"]

        if strategy_name == "vsboss":
             self.strategies["vsboss"] = OneVsBossStrategy()

        strategy = self.strategies[strategy_name]

        for char in self.engine.characters:
            char.health = char.base_hp + sum(i.bonus_hp for i in char.items) 
            char._temp_armor = 0
            char._frozen_turns = 0
            char._doom_counter = None
            char._current_turn_counter = 0

        if strategy_name not in ["2vs2", "5vs5", "vsboss"] and len(self.engine.characters) < 4:
            needed = 4 - len(self.engine.characters)
            if needed > 0:
                random_team = CharGenerator.generate_team(needed)
                for c in random_team:
                    c.name = f"Rand_{c.name}"
                    self.engine.add_character(c)
                self.display.show(f"Added {needed} random fighters to meet the minimum requirement")
        
        all_participants = self.engine.characters

        team1, team2 = strategy.group(all_participants)
        
        if strategy_name == "vsboss":
            if team1 and team2:
                self.display.show(f"\n== BOSS FIGHT START ({team1[0].name} vs {team2[0].name}) ==")
        else:
            self.display.show(f"\n== BATTLE START ({len(team1)} vs {len(team2)} using {strategy_name.upper()}) ==")
            self.display.show(f"Team 1: {[c.name for c in team1]}")
            self.display.show(f"Team 2: {[c.name for c in team2]}")

        turn = 1
        max_turns = 50 if strategy_name == "vsboss" else 30

        while any(c.is_alive() for c in team1) and any(c.is_alive() for c in team2):
            self.display.show(f"\n-- Turn {turn} --")
            
            logs = self.engine.battle_simulation_step(all_participants, strategy)
            
            for log in logs:
                self.display.show(f" > {log}")
            
            if not any(c.is_alive() for c in team1) or not any(c.is_alive() for c in team2):
                break 

            turn += 1
            if turn > max_turns: 
                self.display.show("Draw (Battle took too long)")
                break
        
        self.display.show("\n= BATTLE END =")
        
        winner_team = []
        if any(c.is_alive() for c in team1): winner_team = team1
        elif any(c.is_alive() for c in team2): winner_team = team2
        
        if winner_team:
            names = [c.name for c in winner_team if c.is_alive()]
            self.display.show(f"Winner is Team: {names}")
        else:
            self.display.show("No one won. Everyone died or draw")
            
        for c in self.engine.characters:
            if c.name != "Evil Boss": 
                 self.display.show(Presenter.char_row(c))

class TextAddCommand(Command):
    def __init__(self, doc: Document, display: IDisplay):
        self.doc, self.display = doc, display
    
    def execute(self, args):
        typ = self.display.prompt("Type (h/p): ")
        text = self.display.prompt("Text: ")
        if typ == 'h': self.doc.add(Heading(text))
        else: self.doc.add(Paragraph(text))
        self.display.show("Added")

class TextPrintCommand(Command):
    def __init__(self, doc: Document, display: IDisplay):
        self.doc, self.display = doc, display
    
    def execute(self, args):
        self.display.show(Presenter.doc_view(self.doc.render_full()))

class CreateCharCommand(GameCommand):
    
    def _get_ability_map(self):
        return {
            "1": ("Fireball", lambda dmg: abilities.Fireball(dmg), True, "damage"),
            "2": ("Heal", lambda heal_val: abilities.Heal(heal_val), True, "heal amount"),
            "3": ("Shield", lambda val: abilities.Shield(val, 2), True, "shield amount"), 
            "4": ("Freeze", lambda: abilities.Freeze(1), False, None),
            "5": ("Doom", lambda: abilities.Doom(3), False, None),
            "6": ("Thunderstorm", lambda dmg, turns: abilities.Thunderstorm(dmg, turns), True, "damage"),
            "7": ("BlackHole", lambda dmg, duration: abilities.BlackHole(dmg, duration), True, "damage")
        }

    def _do_execute(self, parsed_args: dict):
        name = self.display.prompt("Name: ")
        if any(c.name == name for c in self.engine.characters):
            return self.display.show(f"Character with name '{name}' already exists")
        
        try:
            hp = int(self.display.prompt("Base HP: "))
            arm = int(self.display.prompt("Base Armor: "))
            atk = int(self.display.prompt("Base Attack: "))
            
            crit_ch_str = self.display.prompt("Crit Chance % (default 10): ")
            crit_ch = float(crit_ch_str) / 100.0 if crit_ch_str else 0.10
            
            crit_mult_str = self.display.prompt("Crit Multiplier % (default 150): ")
            crit_mult = float(crit_mult_str) / 100.0 if crit_mult_str else 1.5

        except ValueError:
            return self.display.show("Invalid number format during initial character stats input. Creation aborted")

        new_char = Character(
            id=name.lower().replace(" ", "_"),
            name=name,
            game="custom",
            level=1,
            stats={
                "max_hp": hp,
                "health": hp,
                "base_hp": hp,
                "attack": atk,
                "base_attack": atk,
                "defense": arm,
                "armor": arm,
                "crit_chance": crit_ch,
                "crit_multiplier": crit_mult
            }
        )
        
        available_abilities = self._get_ability_map()
        
        while True:
            self.display.show("\n- Choose Ability to Add -")
            
            for key, (ab_name, _, needs_param, param_desc) in available_abilities.items():
                param_info = f" (Needs {param_desc})" if needs_param else ""
                self.display.show(f"[{key}] {ab_name}{param_info}")
                
            self.display.show("[0] Finish selecting abilities")

            choice_str = self.display.prompt("Enter ability number or [0] to finish: ").strip() 
            
            if not choice_str:
                self.display.show("Input cannot be empty. Enter number or 0")
                continue
                
            if choice_str == "0":
                break
            
            if choice_str in available_abilities:
                ab_name, ab_factory, needs_param, param_desc = available_abilities[choice_str]
                
                if needs_param:
                    try:
                        param_str = self.display.prompt(f"Enter value for {param_desc} of {ab_name} (default 0): ").strip()
                        param_value = int(param_str) if param_str else 0 
                        
                        if ab_name == "Thunderstorm":
                            new_ability = ab_factory(param_value, 5) 
                        elif ab_name == "BlackHole":
                            new_ability = ab_factory(param_value, 4)
                        else:
                            new_ability = ab_factory(param_value)
                        
                        new_char.abilities.append(new_ability)
                        self.display.show(f"Added ability: {ab_name} (Value: {param_value})")
                        
                    except ValueError:
                        self.display.show("Invalid number format for ability parameter. Please enter a valid integer")
                        continue 
                
                else:
                    new_ability = ab_factory()
                    new_char.abilities.append(new_ability)
                    self.display.show(f"Added ability: {ab_name}")
                    
            else:
                self.display.show("Invalid choice. Please enter a valid number or 0")

        self.engine.add_character(new_char) 
        self.display.show(f"\nCharacter {new_char.name} created successfully!")
        self.display.show(f"- {new_char.name} is ready with {len(new_char.abilities)} abilities! -")

class StartFileManagerCommand(GameCommand):
    def _do_execute(self, parsed_args: dict):
        from cli.filesystem import FileManager
        manager = FileManager(self.display)
        manager.run()
        self.display.show("Returned to Game Menu")