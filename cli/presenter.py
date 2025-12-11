from core.game.models import Character

class Presenter:
    @staticmethod
    def char_row(c: Character) -> str:
        status = "OK" if c.is_alive() else "DEAD"
        if getattr(c, "_frozen_turns", 0) > 0: status = "FROZEN"
        return f"[{status}] {c.name}: HP={c.health}/{c.base_hp} | ARM={c.armor} | ATK={c.attack}"

    @staticmethod
    def doc_view(text: str) -> str:
        return f"================\n{text}\n================"