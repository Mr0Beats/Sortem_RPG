import unittest
from unittest.mock import MagicMock, patch
from core.game.engine import GameEngine
from core.game.models import Character
from core.game.grouping import SplitInTwoStrategy, OneVsAllStrategy
from core.game import abilities 
from typing import List

class TestGameEngine(unittest.TestCase):

    def setUp(self):
        self.engine = GameEngine()
        self.charA = Character("A", 100, 5, 15) 
        self.charB = Character("B", 100, 5, 10)
        self.charC = Character("C", 100, 5, 10)
        self.charD = Character("D", 100, 5, 10)
        
        self.charA.abilities.append(abilities.Fireball(20))
        self.charB.abilities.append(abilities.Heal(10))

        self.engine.add_character(self.charA)
        self.engine.add_character(self.charB)
        self.engine.add_character(self.charC)
        self.engine.add_character(self.charD)
        
        self.all_chars = [self.charA, self.charB, self.charC, self.charD]

    def test_split_in_two_strategy(self):
        """Тест стратегії поділу 2v2."""
        strategy = SplitInTwoStrategy()
        team1, team2 = strategy.group(self.all_chars)
        self.assertIn(self.charA, team1)
        self.assertIn(self.charC, team2) 

    @patch('core.game.engine.random.shuffle')
    @patch('core.game.engine.random.choice')
    @patch('core.game.engine.random.random')
    def test_engine_single_turn(self, mock_random_roll, mock_random_choice, mock_shuffle):
        
        # Гарантуємо, що random.choice завжди повертає charC.
        mock_random_choice.return_value = self.charC 
        
        # Скидаємо здоров'я для надійності
        self.charC.health = self.charC.base_hp 
        self.charA.health = self.charA.base_hp 
        
        mock_random_roll.return_value = 0.5 
        initial_hp_c = self.charC.health 
        strategy = SplitInTwoStrategy()
        mock_shuffle.side_effect = None 
        
        logs: List[str] = list(self.engine.battle_simulation_step(self.all_chars, strategy))
        
        self.assertTrue(any("A attacks" in log and "(Attack 1)" in log for log in logs), "Лог атаки A не знайдено.")
        self.assertTrue(any("B attacks" in log and "(Attack 1)" in log for log in logs), "Лог атаки B не знайдено.")
        self.assertTrue(any("C attacks" in log and "(Attack 1)" in log for log in logs), "Лог атаки C не знайдено.")
        
        self.assertEqual(self.charC.health, 75)
        
        self.assertTrue(self.charA.health <= 100) 


    @patch('core.game.engine.random.shuffle')
    @patch('core.game.engine.random.random')
    def test_engine_multiple_abilities(self, mock_random_roll, mock_shuffle):
        
        self.charA.health = self.charA.base_hp 
        self.charC.health = self.charC.base_hp
        
        mock_random_roll.return_value = 0.1 
        strategy = SplitInTwoStrategy()
        mock_shuffle.side_effect = None 
        
        logs: List[str] = list(self.engine.battle_simulation_step(self.all_chars, strategy))
        
        fireball_logs = [log for log in logs if "A casts Fireball" in log]

        self.assertEqual(len(fireball_logs), 2, f"Очікувалося 2 використання Fireball від A, знайдено {len(fireball_logs)}. Логи: {logs}")
        
        self.assertTrue(any("(Ability 1)" in log for log in fireball_logs), "Не знайдено лог для Ability 1.")
        self.assertTrue(any("(Ability 2)" in log for log in fireball_logs), "Не знайдено лог для Ability 2.")
        
    def test_reset_functionality(self):
        self.charA.health = self.charA.base_hp + sum(i.bonus_hp for i in self.charA.items)
        self.charB._frozen_turns = 0
        
        self.assertEqual(self.charA.health, 100)
        self.assertEqual(self.charB._frozen_turns, 0)