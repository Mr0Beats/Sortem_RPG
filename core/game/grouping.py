from abc import ABC, abstractmethod
from typing import List, Tuple
from .models import Character 

class IGroupingStrategy(ABC):
    @abstractmethod
    def group(self, characters: List[Character]) -> Tuple[List[Character], List[Character]]:
        raise NotImplementedError

class SplitInTwoStrategy(IGroupingStrategy):
    def group(self, characters: List[Character]) -> Tuple[List[Character], List[Character]]:
        if len(characters) < 2:
            return [], []
        
        mid = len(characters) // 2
        return characters[:mid], characters[mid:]

class OneVsAllStrategy(IGroupingStrategy):
    def group(self, characters: List[Character]) -> Tuple[List[Character], List[Character]]:
        if len(characters) < 3:
            return [], []
        
        return [characters[0]], characters[1:]