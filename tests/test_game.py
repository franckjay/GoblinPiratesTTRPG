import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
import io

# To run: python -m unittest tests/test_game.py
OPENAI_API_KEY = "sk-proj-GOBLIN-KEY"
os.environ["OPENAI_API_KEY"] = OPENAI_API_KEY
# Add the project root directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.models import PlayerCharacter, GoblinShip, TargetShip
from src.agents import (
    PlayerCharacterCreation,
    NarrativeAgent,
    DiceAgent,
    ShipCombatAgent,
    BoardingCombatAgent,
    BuildTargetShipAgent
)

class MockLLMResponse:
    def __init__(self, content):
        self.choices = [MagicMock(message=MagicMock(content=content))]

class TestPlayerCharacterCreation(unittest.TestCase):
    def setUp(self):
        self.name = "Grimtooth"
        self.origin_story = "A goblin who learned to fight by wrestling with his pet crocodile"
        self.creator = PlayerCharacterCreation(self.name, self.origin_story)
    
    @patch('src.agents.GameMasterAgent.call_llm')
    @patch('builtins.open', create=True)
    def test_generate_signature_loot(self, mock_open, mock_call_llm):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock loot generation
        mock_call_llm.return_value = "A rusty cutlass that whispers pirate shanties"
        
        # Suppress print output
        with patch('sys.stdout', new=io.StringIO()):
            loot = self.creator.generate_signature_loot()
        
        self.assertEqual(loot, "A rusty cutlass that whispers pirate shanties")

class TestPlayerCharacter(unittest.TestCase):
    def setUp(self):
        self.character = PlayerCharacter(
            name="Grimtooth",
            origin_story="A goblin who learned to fight by wrestling with his pet crocodile",
            strength=2,
            cunning=1,
            marksmanship=0,
            signature_loot="A rusty cutlass that whispers pirate shanties"
        )
    
    def test_character_creation(self):
        self.assertEqual(self.character.name, "Grimtooth")
        self.assertEqual(self.character.origin_story, "A goblin who learned to fight by wrestling with his pet crocodile")
        self.assertEqual(self.character.strength, 2)
        self.assertEqual(self.character.cunning, 1)
        self.assertEqual(self.character.marksmanship, 0)
        self.assertEqual(self.character.signature_loot, "A rusty cutlass that whispers pirate shanties")
        self.assertTrue(self.character.living)
    
    def test_get_summary(self):
        expected_summary = (
            "Name: Grimtooth\n"
            "Origin Story: A goblin who learned to fight by wrestling with his pet crocodile\n"
            "Strength: 2\n"
            "Cunning: 1\n"
            "Marksmanship: 0\n"
            "Signature Loot: A rusty cutlass that whispers pirate shanties"
        )
        self.assertEqual(self.character.get_summary(), expected_summary)

class TestShipCombat(unittest.TestCase):
    def setUp(self):
        self.goblin_ship = GoblinShip("The Squeaky Plank")
        self.target_ship = TargetShip(8, "A mighty warship with golden trim")
        self.dice_agent = DiceAgent()
        self.ship_combat_agent = ShipCombatAgent()
        self.player = PlayerCharacter(
            "Grimtooth",
            "A goblin who learned to fight by wrestling with his pet crocodile",
            2, 1, 0,
            "A rusty cutlass that whispers pirate shanties"
        )

    @patch('src.agents.GameMasterAgent.call_llm')
    @patch('builtins.open', create=True)
    def test_ship_combat_success(self, mock_open, mock_call_llm):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock successful attack narrative
        mock_call_llm.return_value = "The Squeaky Plank's cannons roar as Grimtooth expertly aims at the warship's hull!"
        
        # Mock dice rolls
        with patch.object(self.dice_agent, 'roll_2d6') as mock_roll:
            mock_roll.side_effect = [10, 4]  # Attack roll 10, defense roll 4
            
            # Suppress print output
            with patch('sys.stdout', new=io.StringIO()):
                self.ship_combat_agent.resolve_combat(
                    self.goblin_ship,
                    self.target_ship,
                    self.dice_agent,
                    self.player,
                    "Fire the cannons!"
                )
            
            # Check damage was applied
            self.assertLess(self.target_ship.hull, 20)
            self.assertTrue(self.target_ship.boardable)

    @patch('src.agents.GameMasterAgent.call_llm')
    @patch('builtins.open', create=True)
    def test_ship_combat_escape(self, mock_open, mock_call_llm):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock escape narrative
        mock_call_llm.return_value = "The warship's crew expertly maneuvers to escape the battle!"
        
        # Mock dice rolls for escape
        with patch.object(self.dice_agent, 'roll_2d6') as mock_roll:
            mock_roll.side_effect = [8, 12]  # Attack roll 8, defense roll 12
            
            # Suppress print output
            with patch('sys.stdout', new=io.StringIO()):
                self.ship_combat_agent.resolve_combat(
                    self.goblin_ship,
                    self.target_ship,
                    self.dice_agent,
                    self.player,
                    "Fire the cannons!"
                )
            
            self.assertTrue(self.target_ship.escaped)

class TestBoardingCombat(unittest.TestCase):
    def setUp(self):
        self.target_ship = TargetShip(8, "A mighty warship with golden trim")
        self.dice_agent = DiceAgent()
        self.boarding_agent = BoardingCombatAgent(
            ["A goblin who learned to fight by wrestling with his pet crocodile"],
            "The Squeaky Plank's story"
        )
        self.player = PlayerCharacter(
            "Grimtooth",
            "A goblin who learned to fight by wrestling with his pet crocodile",
            2, 1, 0,
            "A rusty cutlass that whispers pirate shanties"
        )

    @patch('src.agents.GameMasterAgent.call_llm')
    @patch('builtins.open', create=True)
    def test_boarding_combat_success(self, mock_open, mock_call_llm):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock successful boarding narrative
        mock_call_llm.return_value = "Grimtooth leaps onto the enemy ship, his rusty cutlass singing a battle shanty!"
        
        # Mock dice rolls for successful attack
        with patch.object(self.dice_agent, 'roll_2d6') as mock_roll:
            mock_roll.side_effect = [10, 4]  # Attack roll 10, defense roll 4
            
            # Suppress print output
            with patch('sys.stdout', new=io.StringIO()):
                self.boarding_agent.resolve_boarding_combat(
                    self.player,
                    self.target_ship,
                    self.dice_agent,
                    "Charge the enemy!"
                )
            
            # Check damage was applied and player survived
            self.assertLess(self.target_ship.hull, 20)
            self.assertTrue(self.player.living)

    @patch('src.agents.GameMasterAgent.call_llm')
    @patch('builtins.open', create=True)
    def test_boarding_combat_death(self, mock_open, mock_call_llm):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock death narrative
        mock_call_llm.return_value = "Grimtooth's final battle cry echoes across the waves as he falls in battle!"
        
        # Mock dice rolls for death
        with patch.object(self.dice_agent, 'roll_2d6') as mock_roll:
            mock_roll.side_effect = [6, 12]  # Attack roll 6, defense roll 12
            
            # Suppress print output
            with patch('sys.stdout', new=io.StringIO()):
                self.boarding_agent.resolve_boarding_combat(
                    self.player,
                    self.target_ship,
                    self.dice_agent,
                    "Charge the enemy!"
                )
            
            self.assertFalse(self.player.living)

class TestTargetShipGeneration(unittest.TestCase):
    def setUp(self):
        self.target_ship_agent = BuildTargetShipAgent()

    @patch('src.agents.GameMasterAgent.call_llm')
    @patch('builtins.open', create=True)
    def test_generate_target_ship(self, mock_open, mock_call_llm):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock ship description
        mock_call_llm.return_value = "A mighty warship with golden trim, its decks gleaming with the promise of treasure!"
        
        # Suppress print output
        with patch('sys.stdout', new=io.StringIO()):
            ship = self.target_ship_agent.generate_target_ship(8, "The goblins are searching for treasure")
        
        self.assertEqual(ship.difficulty, 8)
        self.assertEqual(ship.hull, 8)  # Hull should equal difficulty
        self.assertFalse(ship.boardable)
        self.assertFalse(ship.escaped)

class TestNarrativeAgent(unittest.TestCase):
    def setUp(self):
        self.narrative_agent = NarrativeAgent(
            ["A goblin who learned to fight by wrestling with his pet crocodile"],
            "The Squeaky Plank's story"
        )

    @patch('src.agents.GameMasterAgent.call_llm')
    @patch('builtins.open', create=True)
    def test_create_initial_narrative(self, mock_open, mock_call_llm):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock initial narrative
        mock_call_llm.return_value = "The goblin pirates set sail on their trusty ship, The Squeaky Plank, in search of adventure and treasure!"
        
        # Suppress print output
        with patch('sys.stdout', new=io.StringIO()):
            narrative = self.narrative_agent.create_initial_narrative()
        
        self.assertIsInstance(narrative, str)
        self.assertGreater(len(narrative), 0)

    @patch('src.agents.GameMasterAgent.call_llm')
    @patch('builtins.open', create=True)
    def test_game_should_end(self, mock_open, mock_call_llm):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock end game decision
        mock_call_llm.return_value = "YES"
        
        # Suppress print output
        with patch('sys.stdout', new=io.StringIO()):
            should_end = self.narrative_agent.game_should_end()
        
        self.assertTrue(should_end)

if __name__ == '__main__':
    unittest.main() 