from core.game.models import Character as CoreCharacter
from infra.api_importer.entities import Character as ImportedCharacter, Item
from typing import Dict, Any

def map_stats(stats: Dict[str, float | int | None]) -> Dict[str, float | int]:

    if stats.get("Health") is not None and stats.get("Attack") is not None:
        try:
            return {
                "health": int(stats["Health"]),
                "attack": int(stats["Attack"]),
                "defense": int(stats.get("Defense", 0) / 10) 
            }
        except (TypeError, ValueError):
             return {"health": 1500, "attack": 200, "defense": 15}


    base_hp = 1000 
    base_attack = 100
    base_defense = 50

    strength = int(stats.get("Strength", 0) or 0)
    vitality = int(stats.get("Vitality", 0) or 0)
    avg_item_level = int(stats.get("average_item_level", 0) or 0)

    hp_mod = int(stats.get("HP", 0) or 0) // 100 
    atk_mod = int(stats.get("Strength", 0) or 0) // 50 
    
    if avg_item_level:
        hp_mod += avg_item_level // 20
        atk_mod += avg_item_level // 10
    
    return {
        "health": base_hp + hp_mod,
        "attack": base_attack + atk_mod,
        "defense": base_defense 
    }

def map_imported_character_to_core(imported_char: ImportedCharacter) -> CoreCharacter:
    
    mapped_stats = map_stats(imported_char.stats)
    
    core_char = CoreCharacter(
        name=imported_char.name,
        hp=mapped_stats["health"],
        armor=mapped_stats["defense"], 
        atk=mapped_stats["attack"]
    )
    
    
    if imported_char.metadata:
        core_char.metadata.update(imported_char.metadata) 

    core_char.metadata["game_source"] = imported_char.game
    core_char.metadata["external_id"] = imported_char.id
    core_char.metadata["external_level"] = imported_char.level

    if imported_char.skills:
        core_char.metadata["external_skills_simple"] = [s.name for s in imported_char.skills]
    
    return core_char