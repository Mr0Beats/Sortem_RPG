from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Optional, List, Any
from infra.persistence import PersistenceService 
from core.game.models import Character 

if TYPE_CHECKING:
    from infra.io import IDisplay
    from core.game.engine import GameEngine

class GameSession:
    def __init__(self, engine: 'GameEngine', display: 'IDisplay'):
        self.engine = engine
        self.display = display
        self.active_char: Optional[Character] = None
        
        self.history: List[str] = []
        self.target_char: Optional[Character] = None 
        
        self.current_state: GameState = CharacterSelectionState(self)
        self.is_running = True

    def log(self, message: str):
        self.history.append(message)
        self.display.show(f"[LOG] {message}")

    def change_state(self, new_state: 'GameState'):
        self.current_state = new_state
        self.current_state.render()

    def handle_input(self, inp: str):
        self.current_state.handle_input(inp)
    
    def run(self):
        self.display.show("\n== STARTING GAME SESSION ==")
        
        self.target_char = Character("Evil Boss", 1500, 10, 50) 
        self.log(f"New enemy {self.target_char.name} appeared!")
        
        self.is_running = True
        self.current_state.render()
        
        while self.is_running:
            try:
                inp = self.display.prompt("GAME > ").strip()
                if not inp: continue
                self.handle_input(inp)
            except KeyboardInterrupt:
                self.display.show("Game interrupted")
                self.is_running = False
                
        self.display.show("Game session ended")

class GameState(ABC):
    def __init__(self, session: GameSession):
        self.session = session

    @abstractmethod
    def render(self):
        pass

    @abstractmethod
    def handle_input(self, inp: str):
        pass

class CharacterSelectionState(GameState):
    def render(self):
        self.session.display.show("\n-- START NEW GAME --")
        self.session.display.show("Available characters:")
        
        if not self.session.engine.characters:
            self.session.display.show("No characters. Use 'create' or 'import' in the main menu")
            self.session.is_running = False
            return
            
        for c in self.session.engine.characters:
            self.session.display.show(f"- {c.name} (HP: {c.health})")
        self.session.display.show("\nEnter character name to start or type 'quit' to exit")

    def handle_input(self, inp: str):
        if inp.lower() == 'quit':
            self.session.is_running = False
            return

        char = self.session.engine.get_character_by_name(inp)
        if char:
            self.session.active_char = char
            self.session.log(f"Player selected {char.name}")
            self.session.change_state(PlayingState(self.session))
        else:
            self.session.display.show(f"Character '{inp}' not found")

class PlayingState(GameState):
    def render(self):
        c = self.session.active_char
        t = self.session.target_char
        
        if not c or not t:
             self.session.display.show("Error: Character or Target is missing")
             self.session.is_running = False
             return
             
        self.session.display.show(f"\n-- GAME TURN --")
        self.session.display.show(f"You: **{c.name}** (HP: {c.health}/{c.base_hp} | ATK: {c.attack} | ARM: {c.armor})")
        self.session.display.show(f"Enemy: **{t.name}** (HP: {t.health}/{t.base_hp} | ARM: {t.armor})")
        self.session.display.show("Commands: attack, status, save, history, quit")

    def handle_input(self, inp: str):
        parts = inp.split()
        cmd = parts[0].lower()
        args = parts[1:]

        if cmd == 'quit':
            self.session.display.show("Game session closed")
            self.session.is_running = False
            
        elif cmd == 'save':
            all_chars = [self.session.active_char, self.session.target_char] + self.session.engine.characters
            if PersistenceService.save_game([c for c in all_chars if c is not None], self.session.history):
                self.session.display.show("Game state saved successfully!")
            else:
                 self.session.display.show("Error saving game state")

        elif cmd == 'history':
            self.session.display.show("\n-- Battle History --")
            for record in self.session.history:
                 self.session.display.show(f" > {record}")
            
        elif cmd == 'status':
            self.render()
            
        elif cmd == 'attack':
            self._handle_action(args)

        else:
            self.session.display.show("Unknown game command")

    def _handle_action(self, args: list):
        c = self.session.active_char
        t = self.session.target_char
        
        if not c or not t: return

        if c.is_alive() and t.is_alive():
            res = c.calculate_damage(t)
            self.session.log(res['log'])
            c.end_turn_update()
        
        if not t.is_alive():
            self.session.display.show(f"**{c.name}** defeated {t.name}! You Win!")
            self.session.change_state(GameOverState(self.session))
            return
        
        if t.is_alive():
            t_res = t.calculate_damage(c, ability_mod=0.8) 
            self.session.log(t_res['log'])
            t.end_turn_update()
        
        if not c.is_alive():
            self.session.display.show(f"**{c.name}** was defeated by {t.name}. Game Over!")
            self.session.change_state(GameOverState(self.session))
            return
            
        self.render()

class GameOverState(GameState):
    def render(self):
        self.session.display.show("\n-- GAME OVER --")
        self.session.display.show("Type 'quit' to return to main menu")

    def handle_input(self, inp: str):
        if inp.lower() == 'quit':
            self.session.is_running = False
        else:
            self.session.display.show("Please type 'quit'")