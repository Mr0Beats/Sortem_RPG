import json
import dataclasses
from pathlib import Path
from typing import List
from infra.api_importer.entities import Character, Skill, Item

SAVE_FILE = Path("data/savegame.json")

class GameStorage:
    @staticmethod
    def save_game(characters: List[Character]):
        data_to_save = []
        
        for char in characters:
            char_dict = dataclasses.asdict(char)
            data_to_save.append(char_dict)
        
        SAVE_FILE.parent.mkdir(parents=True, exist_ok=True)
        
        try:
            with open(SAVE_FILE, "w", encoding="utf-8") as f:
                json.dump(data_to_save, f, indent=4, ensure_ascii=False)
            print(f"Game saved to {SAVE_FILE}")
        except Exception as e:
            print(f"Save failed: {e}")

    @staticmethod
    def load_game() -> List[Character]:
        if not SAVE_FILE.exists():
            print("No save file found")
            return []
            
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                raw_data = json.load(f)
            
            loaded_chars = []
            for char_data in raw_data:
                skills_data = char_data.get("skills", [])
                restored_skills = [Skill(**s) for s in skills_data] 

                items_data = char_data.get("equipment", [])
                restored_items = [Item(**i) for i in items_data]

                char_data["skills"] = restored_skills
                char_data["equipment"] = restored_items
                
                character = Character(**char_data)
                loaded_chars.append(character)
            
            print(f"Loaded {len(loaded_chars)} characters from save")
            return loaded_chars

        except Exception as e:
            print(f"Load failed: {e}")
            return []