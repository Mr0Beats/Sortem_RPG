import requests
import os
from functools import lru_cache
from typing import Dict, Any

from .entities import Character, Skill
from infra.image_loader import cache_image

GENSHIN_API_URL = "https://genshin.jmp.blue"

BASE_STATS_MOCK = {
    "max_hp": 15000,
    "attack": 350,
    "defense": 800
}

def get_genshin_icon_url(char_slug: str) -> str:
    return f"{GENSHIN_API_URL}/characters/{char_slug}/icon-big"

@lru_cache(maxsize=50)
def fetch_genshin_character(name: str, level: int = 90) -> Character:
    name_slug = name.lower().replace(' ', '-')
    char_url = f"{GENSHIN_API_URL}/characters/{name_slug}"

    try:
        response = requests.get(char_url)
        if response.status_code == 404:
            raise ValueError(f"Genshin Character '{name}' not found. Check spelling")
        
        response.raise_for_status() 
        data: Dict[str, Any] = response.json()

    except requests.exceptions.RequestException as e:
        raise Exception(f"Network error during Genshin API request: {e}")

    remote_url = get_genshin_icon_url(name_slug)
    
    print(f"DEBUG: Downloading image for {name} from {remote_url}")
    local_icon_path = cache_image(remote_url, name)
    print(f"DEBUG: Saved raw path: {local_icon_path}")

    web_icon_path = local_icon_path.replace("\\", "/")
    
    if "data/" in web_icon_path:
        web_icon_path = web_icon_path[web_icon_path.find("data/"):]

    level_multiplier = level / 90 
    final_stats: Dict[str, Any] = {
        key: int(value * level_multiplier)
        for key, value in BASE_STATS_MOCK.items()
    }

    skill_talents_data = data.get("skillTalents", []) 
    skills = []
    if isinstance(skill_talents_data, list):
        for t in skill_talents_data:
            s_name = t.get("name", "Unknown Talent")
            unlock_type = t.get("unlock", "Normal Attack")
            
            full_name = f"{unlock_type}: {s_name}"
            
            skills.append(
                Skill(
                    id=s_name.lower().replace(" ", "_"), 
                    name=full_name,
                    description=t.get("description", "No description")
                ) 
            )

    core_char = Character(
        id=data.get("id", name_slug),
        name=data.get("name", name),
        game="genshin",
        level=level,
        stats=final_stats,
        skills=skills,
        equipment=[], 
        metadata={
            "vision": data.get("vision", "Unknown"),
            "weapon_type": data.get("weapon", "Unknown"),
            "description": data.get("description", ""),
            "rarity": data.get("rarity", 4),
            "ui_assets": {
                "remote_url": remote_url,
                "icon_url": web_icon_path,
                "element_img": f"elements/{data.get('vision', 'anemo').lower()}.png"
            }
        }
    )
    return core_char