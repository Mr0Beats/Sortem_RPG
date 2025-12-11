from abc import ABC, abstractmethod

class IDisplay(ABC):
    @abstractmethod
    def show(self, msg: str): pass
    @abstractmethod
    def prompt(self, msg: str) -> str: pass

class ConsoleDisplay(IDisplay):
    def show(self, msg: str):
        print(msg)
    def prompt(self, msg: str) -> str:
        return input(msg)