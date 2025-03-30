import unittest
from unittest.mock import patch, MagicMock
import json
import sys
import os
OPENAI_API_KEY = "sk-proj-00000000000000000000000000000000"
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
    
    @patch('src.agents.OpenAI')
    @patch('builtins.open', create=True)
    def test_generate_character(self, mock_open, mock_openai):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock successful character generation
        mock_response = {
            "strength": 2,
            "cunning": 1,
            "marksmanship": 0,
            "signature_loot": "A rusty cutlass that whispers pirate shanties"
        }
        mock_openai.return_value.chat.completions.create.return_value = MockLLMResponse(json.dumps(mock_response))
        
        character = self.creator.generate_character()
        
        self.assertEqual(character.name, self.name)
        self.assertEqual(character.origin_story, self.origin_story)
        self.assertEqual(character.strength, 2)
        self.assertEqual(character.cunning, 1)
        self.assertEqual(character.marksmanship, 0)
        self.assertEqual(character.signature_loot, "A rusty cutlass that whispers pirate shanties")
        self.assertTrue(character.living)

    @patch('src.agents.OpenAI')
    @patch('builtins.open', create=True)
    def test_generate_unbalanced_goblin(self, mock_open, mock_openai):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock failed character generation to trigger unbalanced goblin
        mock_openai.return_value.chat.completions.create.return_value = MockLLMResponse("Invalid JSON")
        
        character = self.creator.generate_character()
        
        # Check that stats sum to 3 and one stat is 2, one is 1, and one is 0
        stats = [character.strength, character.cunning, character.marksmanship]
        self.assertEqual(sum(stats), 3)
        self.assertEqual(max(stats), 2)
        self.assertEqual(min(stats), 0)
        self.assertTrue(1 in stats)

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

    @patch('src.agents.OpenAI')
    @patch('builtins.open', create=True)
    def test_ship_combat_success(self, mock_open, mock_openai):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock successful attack narrative
        mock_openai.return_value.chat.completions.create.return_value = MockLLMResponse(
            "The Squeaky Plank's cannons roar as Grimtooth expertly aims at the warship's hull!"
        )
        
        # Mock dice rolls
        with patch.object(self.dice_agent, 'roll_2d6') as mock_roll:
            mock_roll.side_effect = [10, 4]  # Attack roll 10, defense roll 4
            
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

    @patch('src.agents.OpenAI')
    @patch('builtins.open', create=True)
    def test_ship_combat_escape(self, mock_open, mock_openai):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock escape narrative
        mock_openai.return_value.chat.completions.create.return_value = MockLLMResponse(
            "The warship's crew expertly maneuvers to escape the battle!"
        )
        
        # Mock dice rolls for escape
        with patch.object(self.dice_agent, 'roll_2d6') as mock_roll:
            mock_roll.side_effect = [8, 12]  # Attack roll 8, defense roll 12
            
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

    @patch('src.agents.OpenAI')
    @patch('builtins.open', create=True)
    def test_boarding_combat_success(self, mock_open, mock_openai):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock successful boarding narrative
        mock_openai.return_value.chat.completions.create.return_value = MockLLMResponse(
            "Grimtooth leaps onto the enemy ship, his rusty cutlass singing a battle shanty!"
        )
        
        # Mock dice rolls for successful attack
        with patch.object(self.dice_agent, 'roll_2d6') as mock_roll:
            mock_roll.side_effect = [10, 4]  # Attack roll 10, defense roll 4
            
            self.boarding_agent.resolve_boarding_combat(
                self.player,
                self.target_ship,
                self.dice_agent,
                "Charge the enemy!"
            )
            
            # Check damage was applied and player survived
            self.assertLess(self.target_ship.hull, 20)
            self.assertTrue(self.player.living)

    @patch('src.agents.OpenAI')
    @patch('builtins.open', create=True)
    def test_boarding_combat_death(self, mock_open, mock_openai):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock death narrative
        mock_openai.return_value.chat.completions.create.return_value = MockLLMResponse(
            "Grimtooth's final battle cry echoes across the waves as he falls in battle!"
        )
        
        # Mock dice rolls for death
        with patch.object(self.dice_agent, 'roll_2d6') as mock_roll:
            mock_roll.side_effect = [6, 12]  # Attack roll 6, defense roll 12
            
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

    @patch('src.agents.OpenAI')
    @patch('builtins.open', create=True)
    def test_generate_target_ship(self, mock_open, mock_openai):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock ship description
        mock_openai.return_value.chat.completions.create.return_value = MockLLMResponse(
            "A mighty warship with golden trim, its decks gleaming with the promise of treasure!"
        )
        
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

    @patch('src.agents.OpenAI')
    @patch('builtins.open', create=True)
    def test_create_initial_narrative(self, mock_open, mock_openai):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock initial narrative
        mock_openai.return_value.chat.completions.create.return_value = MockLLMResponse(
            "The goblin pirates set sail on their trusty ship, The Squeaky Plank, in search of adventure and treasure!"
        )
        
        narrative = self.narrative_agent.create_initial_narrative()
        
        self.assertIsInstance(narrative, str)
        self.assertGreater(len(narrative), 0)

    @patch('src.agents.OpenAI')
    @patch('builtins.open', create=True)
    def test_game_should_end(self, mock_open, mock_openai):
        # Mock file operations
        mock_open.return_value.__enter__.return_value.read.return_value = "Mock content"
        
        # Mock end game decision
        mock_openai.return_value.chat.completions.create.return_value = MockLLMResponse("YES")
        
        should_end = self.narrative_agent.game_should_end()
        
        self.assertTrue(should_end)

if __name__ == '__main__':
    unittest.main() 