import unittest
from core.game.models import Character, Item
from core.game.abilities import Fireball, Freeze, Doom, BrainSap, DarkBlast, Shield, BlackHole
from typing import List

class TestCharacterAndAbilities(unittest.TestCase):

    def setUp(self):
        self.char1 = Character("Hero", 100, 10, 20)
        self.char2 = Character("Enemy", 80, 5, 15)

    def test_base_stats(self):
        self.assertEqual(self.char1.health, 100)
        self.assertEqual(self.char1.armor, 10)
        self.assertEqual(self.char1.attack, 20)

    def test_attack(self):
        self.char1.attack_target(self.char2)
        self.assertEqual(self.char2.health, 80 - 15)
        self.assertTrue(self.char2.is_alive())

    def test_shield(self):
        shield = Shield(bonus=5, duration=2)
        shield.use(self.char1, self.char1)
        self.assertEqual(self.char1.armor, 15)
        
        self.char1.end_turn_update()
        self.char1.end_turn_update()
        self.assertEqual(self.char1.armor, 10)

    def test_doom(self):
        doom = Doom(delay=2)
        doom.use(self.char1, self.char2)
        self.assertEqual(self.char2._doom_counter, 2)
        
        logs: List[str] = self.char2.end_turn_update()
        self.assertNotIn("DOOM claims", logs) 
        self.assertEqual(self.char2.health, 80)
        
        logs = self.char2.end_turn_update()
        self.assertIn("DOOM claims", logs[0])
        self.assertEqual(self.char2.health, 0)
        self.assertFalse(self.char2.is_alive())

    def test_dark_blast_cooldown(self):
        blast = DarkBlast(damage=100, min_turn=3)
        
        log1 = blast.use(self.char1, self.char2)
        self.assertIn("Available from turn 3", log1)
        
        self.char1.end_turn_update() 
        
        log2 = blast.use(self.char1, self.char2)
        self.assertIn("Available from turn 3", log2)

        self.char1.end_turn_update() 

        log3 = blast.use(self.char1, self.char2)
        self.assertNotIn("Available from turn 3", log3)
        
    def test_black_hole(self):
        hole = BlackHole(damage=50, min_turn=1) 
        
        hole.use(self.char1, self.char2)
        self.assertEqual(self.char2.health, 80 - 45)
        self.assertEqual(self.char2._frozen_turns, 1)

    def test_brain_sap_cooldown(self):
        brain_sap = BrainSap(damage=50, cooldown=3)
        
        log1 = brain_sap.use(self.char1, self.char2)
        self.assertIn("drains mind", log1)

        self.char1.end_turn_update() 
        
        log2 = brain_sap.use(self.char1, self.char2)
        self.assertIn("fails BrainSap (Cooldown: 2 turns)", log2)

        self.char1.end_turn_update() 
        self.char1.end_turn_update() 

        log3 = brain_sap.use(self.char1, self.char2)
        self.assertIn("drains mind", log3)