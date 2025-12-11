from .genshin_adapter import fetch_genshin_character 
from .entities import Character

def import_character(source: str, **kwargs) -> Character:

    if source == "genshin":
        if "name" not in kwargs:
             raise ValueError("Missing 'name' for genshin source")
        
        return fetch_genshin_character(kwargs["name"], int(kwargs.get("level", 90)))
        
    raise ValueError(f"Unknown source: {source}. Only 'genshin' is supported")