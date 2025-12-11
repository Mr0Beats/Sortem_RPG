import sys
import json
import os
from typing import List, Dict, Any, Tuple
from dataclasses import asdict, is_dataclass
from pathlib import Path

from infra.api_importer.entities import Character, Skill, Item 

if getattr(sys, 'frozen', False):
    BASE_DIR = Path(sys.executable).parent
else:
    BASE_DIR = Path(__file__).resolve().parent.parent 

DATA_DIR = BASE_DIR / "data"
DATA_FILE = DATA_DIR / 'game_data.json'
SAVE_GAME_FILE = DATA_DIR / 'game_save.json'

class PersistenceService:
    
    @staticmethod
    def _extract_stat(obj: Any, keys: List[str], default: int = 0) -> int:
        stats_dict = getattr(obj, "stats", {}) or {}
        for key in keys:
            if key in stats_dict and stats_dict[key]:
                return stats_dict[key]
        
        for key in keys:
            if hasattr(obj, key):
                val = getattr(obj, key)
                if val: return val
                
        return default

    @staticmethod
    def _char_to_dict(c: Any) -> Dict[str, Any]:
        
        real_hp = PersistenceService._extract_stat(c, ["max_hp", "base_hp", "hp", "health"], 100)
        real_atk = PersistenceService._extract_stat(c, ["attack", "base_attack", "atk", "strength"], 10)
        real_def = PersistenceService._extract_stat(c, ["defense", "armor", "base_armor"], 0)
        
        final_stats = {
            "max_hp": real_hp,
            "health": real_hp,
            "attack": real_atk,
            "defense": real_def,
            "speed": PersistenceService._extract_stat(c, ["speed"], 10),
            "energy": PersistenceService._extract_stat(c, ["energy"], 0),
            "level": getattr(c, "level", 1)
        }

        safe_skills = []
        if hasattr(c, "skills"):
            for s in c.skills:
                if is_dataclass(s):
                    safe_skills.append(asdict(s))
                elif isinstance(s, dict):
                    safe_skills.append(s)
                else:
                    safe_skills.append({
                        "name": getattr(s, "name", "Unknown Skill"),
                        "description": getattr(s, "description", ""),
                        "damage": getattr(s, "value", getattr(s, "damage", 0))
                    })

        return {
            "id": getattr(c, "id", getattr(c, "name", "unknown").lower()),
            "name": getattr(c, "name", "Unknown"),
            "game": getattr(c, "game", "custom"),
            "level": getattr(c, "level", 1),
            "stats": final_stats,
            "skills": safe_skills,
            "equipment": [],
            "metadata": getattr(c, "metadata", {})
        }

    @staticmethod
    def _dict_to_char(d: Dict[str, Any]) -> Character:
        skills_list = []
        for s in d.get("skills", []):
            try:
                if isinstance(s, dict):
                    skills_list.append(Skill(**s))
                else:
                    skills_list.append(s)
            except Exception:
                pass

        saved_stats = d.get("stats", {})
        
        hp = saved_stats.get("max_hp", d.get("max_hp", 100))
        atk = saved_stats.get("attack", d.get("attack", 10))
        defense = saved_stats.get("defense", d.get("armor", 0))
        level = d.get("level", saved_stats.get("level", 1))

        reconstructed_stats = {
            "max_hp": hp,
            "base_hp": hp,
            "health": hp,
            "hp": hp,
            "attack": atk,
            "base_attack": atk,
            "defense": defense,
            "armor": defense,
            "speed": saved_stats.get("speed", 10),
            "energy": saved_stats.get("energy", 0)
        }
        
        d["stats"] = reconstructed_stats
        d["skills"] = skills_list
        d["level"] = level

        try:
            return Character(**d)
        except TypeError:
            return Character(
                id=d.get("id", d.get("name", "").lower()),
                name=d.get("name", "Unknown"),
                game=d.get("game", "custom"),
                level=level,
                stats=reconstructed_stats,
                skills=skills_list,
                equipment=[],
                metadata=d.get("metadata", {})
            )

    @staticmethod
    def save_characters(characters: List[Character]) -> bool:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        
        print(f"DEBUG: Saving to {DATA_FILE}")
        
        data = [PersistenceService._char_to_dict(c) for c in characters] 
        try:
            with open(DATA_FILE, 'w', encoding='utf-8') as f:
                json.dump({"characters": data}, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Error saving catalog: {e}")
            return False

    @staticmethod
    def load_characters() -> List[Character]:
        if not DATA_FILE.exists():
            print(f"DEBUG: File not found at {DATA_FILE}")
            return []
        try:
            with open(DATA_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                chars = data.get("characters", [])
                print(f"DEBUG: Loaded {len(chars)} characters from JSON")
                return [PersistenceService._dict_to_char(d) for d in chars]
        except Exception as e:
            print(f"Error loading catalog: {e}")
            return []
            
    @staticmethod
    def save_game(characters: List[Character], history: List[str]) -> bool:
        DATA_DIR.mkdir(parents=True, exist_ok=True)
        data = {
            "session_characters": [PersistenceService._char_to_dict(c) for c in characters],
            "history": history,
        }
        try:
            with open(SAVE_GAME_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"Game Save Error: {e}")
            return False
            
    @staticmethod
    def load_game() -> Tuple[List[Character], List[str]]:
        if not SAVE_GAME_FILE.exists():
             return [], []
        try:
            with open(SAVE_GAME_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
            loaded_chars = [PersistenceService._dict_to_char(d) for d in data.get("session_characters", [])]
            return loaded_chars, data.get("history", [])
        except Exception as e:
            print(f"Game Load Error: {e}")
            return [], []