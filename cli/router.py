from typing import Dict, List, Optional
from abc import ABC, abstractmethod
from cli.commands import Command

class CommandHandler(ABC):
    @abstractmethod
    def set_next(self, handler: 'CommandHandler') -> 'CommandHandler':
        pass

    @abstractmethod
    def handle(self, command: str, args: List[str]) -> bool:
        pass


class Router(CommandHandler):
    def __init__(self):
        self._commands: Dict[str, Command] = {}
        self._next_handler: Optional['CommandHandler'] = None
        
    def set_next(self, handler: 'CommandHandler') -> 'CommandHandler':
        self._next_handler = handler
        return handler

    def register(self, cmd_name: str, command: Command):
        self._commands[cmd_name] = command
    
    def handle(self, command: str, args: List[str]) -> bool:
        if command in self._commands:
            self._commands[command].execute(args)
            return True
        elif self._next_handler:
            return self._next_handler.handle(command, args)
        else:
            return False 

    def handle_input(self, user_input: str):
        parts = user_input.split()
        if not parts: return
        
        command = parts[0]
        args = parts[1:]
        
        if not self.handle(command, args):
             print(f"Unknown command: '{command}'")