import os
import sys
import requests
from pathlib import Path

def get_root_dir():
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent
    else:
        return Path(__file__).resolve().parent.parent.parent

PROJECT_ROOT = get_root_dir()
CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "images"
FILE_PATH = Path(__file__).resolve()
PROJECT_ROOT = FILE_PATH.parent.parent 
CACHE_DIR = PROJECT_ROOT / "data" / "cache" / "images"

ALIASES = {
    "Kaedehara Kazuha": "Kazuha",
    "Kamisato Ayaka": "Ayaka",
    "Kamisato Ayato": "Ayato",
    "Raiden Shogun": "Shougun",
    "Yae Miko": "Yae",
    "Arataki Itto": "Itto",
    "Kuki Shinobu": "Shinobu",
    "Shikanoin Heizou": "Heizou",
    "Hu Tao": "Hutao",
    "Childe": "Tartaglia",
    "Traveler": "PlayerBoy",
}

def ensure_cache_dir():
    if not CACHE_DIR.exists():
        CACHE_DIR.mkdir(parents=True, exist_ok=True)

def get_name_variations(char_name: str) -> list[str]:
    variations = []
    clean_name = char_name.strip()
    
    if clean_name in ALIASES:
        variations.append(ALIASES[clean_name])

    parts = clean_name.split()

    if len(parts) > 1:
        variations.append(parts[-1])
        variations.append(parts[-1].capitalize()) 
        variations.append("".join(parts).capitalize())

    variations.append(clean_name.replace(" ", ""))
    variations.append(clean_name.replace(" ", "").capitalize())
    variations.append(clean_name.replace(" ", "_").lower())
    
    return list(dict.fromkeys(variations))

def cache_image(original_url: str, char_name: str) -> str:
    ensure_cache_dir()
    
    save_filename = f"{char_name.strip().lower().replace(' ', '_')}.png"
    local_path = CACHE_DIR / save_filename
    
    if local_path.exists() and local_path.stat().st_size > 0:
        return str(local_path)

    print(f"⬇ Downloading image for [{char_name}]..")
    
    possible_names = get_name_variations(char_name)
    
    headers = {'User-Agent': 'Mozilla/5.0'}
    
    for name_variant in possible_names:
        
        name_cap = name_variant[0].upper() + name_variant[1:]
        name_lower = name_variant.lower()
        
        sources = [
            f"https://enka.network/ui/UI_AvatarIcon_{name_cap}.png",
            f"https://upload-os-bbs.mihoyo.com/game_record/genshin/character_icon/UI_AvatarIcon_{name_cap}.png",
            f"https://raw.githubusercontent.com/FortOfFans/GenShin/main/icon/{name_lower}.png",
            f"https://api.ambr.top/assets/UI/UI_AvatarIcon_{name_cap}.png"
        ]

        for url in sources:
            try:
                response = requests.get(url, headers=headers, timeout=5)
                
                if response.status_code == 200 and response.content.startswith(b'\x89PNG'):
                    with open(local_path, 'wb') as f:
                        f.write(response.content)
                    print(f" Found as '{name_variant}' -> Saved to cache")
                    return str(local_path)
                    
            except Exception:
                continue

    print(f" Failed to find image for {char_name} (Tried: {possible_names})")
    return original_url