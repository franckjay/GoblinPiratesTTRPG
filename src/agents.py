from abc import ABC, abstractmethod
import os
import json
from openai import OpenAI
from dotenv import load_dotenv
from .models import PlayerCharacter, TargetShip

class GameMasterAgent(ABC):
    """
    Base class for the Game Master agent.
    """
    
    def __init__(self, deep_research: bool = False, max_iterations: int = 3):
        """
        Initialize the GameMasterAgent with OpenAI configuration and game rules.
        
        Args:
            deep_research (bool): Whether to use iterative refinement for responses
            max_iterations (int): Maximum number of refinement iterations (if deep_research is True)
        """
        with open('src/rules/EditableRules.md', 'r') as f:
            self.game_rules = f.read()

        load_dotenv()  # Load environment variables from .env file
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.client = OpenAI(api_key=api_key)
        self.model = "gpt-3.5-turbo"
        self.deep_research = deep_research
        self.max_iterations = max_iterations
    
    def call_llm(self, prompt: str) -> str:
        """
        Call the OpenAI API with the given prompt.
        
        Args:
            prompt (str): The prompt to send to the LLM
            
        Returns:
            str: The LLM's response
        """
        try:
            if not self.deep_research:
                return self._single_call(prompt)
            
            # Deep research mode: iterative refinement
            current_response = self._single_call(prompt)
            
            for _ in range(self.max_iterations - 1):  # -1 because we already have the first response
                refinement_prompt = f"""
                Previous response to the prompt: {current_response}
                
                Please refine this response to maximize:
                1. Player enjoyment and engagement
                2. Narrative cohesiveness with the game's theme and rules
                
                Output only the refined response in the same format as the original, with no explanations.
                """
                
                refined_response = self._single_call(refinement_prompt)
                current_response = refined_response
            
            return current_response
            
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return "I apologize, but I encountered an error processing your request."
    
    def _single_call(self, prompt: str) -> str:
        """
        Make a single call to the OpenAI API.
        
        Args:
            prompt (str): The prompt to send to the LLM
            
        Returns:
            str: The LLM's response
        """
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": "You are a creative and humorous Game Master for a goblin pirate-themed TTRPG."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=5000
        )
        return response.choices[0].message.content
    
    @abstractmethod
    def parse_llm_response(self, response: str):
        raise NotImplementedError("Subclasses must implement this method")

class PlayerCharacterCreation(GameMasterAgent):
    def __init__(self, game_rules: str):
        """
        Initialize the PlayerCharacterCreation agent.
        
        Args:
            game_rules (str): The rules of the game
        """
        super().__init__(game_rules)
        self.prompt_template = self._load_prompt_template()
    
    def _load_prompt_template(self) -> str:
        """Load the character creation prompt template."""
        try:
            with open('generation_prompts/character_creation_prompt.md', 'r') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading prompt template: {e}")
            return "Generate a goblin character based on this origin story: {origin_story}"
    
    def generate_character(self, origin_story: str) -> PlayerCharacter:
        """
        Generate a character based on the origin story using the LLM.
        
        Args:
            origin_story (str): The character's backstory
            
        Returns:
            PlayerCharacter: The generated character
        """
        # Format the prompt with the provided information
        prompt = self.prompt_template.format(
            origin_story=origin_story,
            game_rules=self.game_rules
        )
        
        # Get the LLM response
        response = self.call_llm(prompt)
        
        # Parse the response into a PlayerCharacter object
        return self.parse_llm_response(response)
    
    def parse_llm_response(self, response: str) -> PlayerCharacter:
        """
        Parse the LLM response into a PlayerCharacter object.
        
        Args:
            response (str): The JSON response from the LLM
            
        Returns:
            PlayerCharacter: The parsed character object
        """
        try:
            # Parse the JSON response
            char_data = json.loads(response)
            
            # Validate the required fields
            required_fields = ['name', 'strength', 'cunning', 'marksmanship', 'signature_loot']
            for field in required_fields:
                if field not in char_data:
                    raise ValueError(f"Missing required field: {field}")
            
            # Validate stat ranges
            for stat in ['strength', 'cunning', 'marksmanship']:
                if not 1 <= char_data[stat] <= 3:
                    raise ValueError(f"Stat {stat} must be between 1 and 3")
            
            # Create and return the PlayerCharacter object
            return PlayerCharacter(
                name=char_data['name'],
                origin_story=char_data.get('origin_story', ''),
                strength=char_data['strength'],
                cunning=char_data['cunning'],
                marksmanship=char_data['marksmanship'],
                signature_loot=char_data['signature_loot']
            )
        except json.JSONDecodeError as e:
            print(f"Error parsing LLM response as JSON: {e}")
            raise ValueError("Invalid JSON response from LLM")
        except Exception as e:
            print(f"Error parsing character data: {e}")
            raise ValueError("Failed to create character from LLM response")

class NarrativeAgent(GameMasterAgent):
    def __init__(self, character_stories: list[str]):
    def create_initial_narrative(self, , game_rules: str):
        """Simulates calling an LLM to create an initial game scenario."""
        print(f"Calling LLM: Create a fun and humorous RPG scenario for the goblins.")
        return "Your goblins are on a mission to steal the Moon King's golden crown!"

class BuildTargetShipAgent(GameMasterAgent):
    def generate_target_ship(self, ship_difficulty: int, current_narrative: str):
        """Simulates calling an LLM to generate an enemy ship based on difficulty and story."""
        print(f"Calling LLM: Describe an enemy ship with difficulty {ship_difficulty} fitting this story: {current_narrative}")
        return TargetShip(ship_difficulty, "A Kobold Kruise full of treasure!")

class ShipCombatAgent(GameMasterAgent):
    def resolve_combat(self, overall_story_narrative: str, attacking_ship, target_ship, game_rules: str, roll: int):
        """Simulates calling an LLM to determine the outcome of ship combat."""
        print(f"Calling LLM: Resolve ship combat where goblins try {overall_story_narrative}, roll: {roll}")
        return "The goblins unleash a volley of explosive junk cannons! The enemy ship is now vulnerable."

class BoardingCombatAgent(GameMasterAgent):
    def describe_boarding(self, pc_story_narrative: str, attacking_ship, target_ship, game_rules: str):
        """Simulates calling an LLM to describe the boarding combat setup."""
        print(f"Calling LLM: Describe the goblins boarding {target_ship.narrative}")
        return "The goblins swing aboard, landing in a pile of confused kobolds!"

    def player_turn(self, dice_roll: int, character_input: str, goblin, target_ship):
        """Simulates calling an LLM to describe the player's attack during boarding combat."""
        print(f"Calling LLM: Resolve {goblin.name}'s attack: {character_input} with roll {dice_roll}")
        return f"{goblin.name} swings wildly and... {('lands a hit!' if dice_roll > 7 else 'misses!')}"