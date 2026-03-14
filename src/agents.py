from abc import ABC, abstractmethod
import os
import random
from typing import Tuple

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from pydantic import BaseModel, Field
import sys
from dotenv import load_dotenv
from .models import PlayerCharacter, TargetShip, GoblinShip
from .generation_prompts.loot_prompt import loot_prompt
from .rules.editable_rules import game_rules
import random

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
        self.game_rules = game_rules

        load_dotenv()  # Load environment variables from .env file
        api_key = os.getenv('OPENAI_API_KEY')
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")
        
        self.model = "gpt-3.5-turbo"
        self.client = ChatOpenAI(api_key=api_key, model=self.model, temperature=0.7, max_tokens=5000)
        self.system_prompt = "You are a creative and humorous Game Master for a goblin pirate-themed TTRPG."
        self.prompt_template = ChatPromptTemplate.from_messages([
            ("system", self.system_prompt),
            ("user", "{prompt}")
        ])
        self.chain = (self.prompt_template | self.client | StrOutputParser()).with_retry(stop_after_attempt=3)

        # We manage context natively since older LangChain memory was deprecated.
        self.memory: list[str] = []
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
        # If not deep research, simply stream output and return final string
        try:
            full_response = ""
            
            # Gather memory context
            history_context = "\n".join(self.memory)
            
            augmented_prompt = prompt
            if history_context:
                augmented_prompt = f"Previous Story Context:\n{history_context}\n\nNew Request:\n{prompt}"

            for chunk in self.chain.stream({"prompt": augmented_prompt}):
                print(chunk, end="", flush=True)
                full_response += chunk
            print() # Add a newline after the stream finishes

            # Save to memory naturally
            self.memory.append(f"User: {prompt}\nAgent: {full_response}")
            
            # Prune memory if it gets too large
            while len(self.memory) > 5:
                self.memory.pop(0)

            return full_response
        except Exception as e:
            print(f"Error calling LLM: {e}")
            return "I apologize, but I encountered an error processing your request."
    
    @abstractmethod
    def parse_llm_response(self, response: str) -> str:
        raise NotImplementedError("Subclasses must implement this method")

class DiceAgent:
    """
    Agent responsible for handling all dice rolling operations in the game.
    """
    
    def __init__(self):
        """Initialize the DiceAgent."""
        pass
    
    def roll_2d6(self) -> int:
        """
        Roll two six-sided dice and return their sum.
        
        Returns:
            int: The sum of two d6 rolls (2-12)
        """
        return random.randint(1, 6) + random.randint(1, 6)
    
    def roll_loot_die(self, ship_size: str) -> int:
        """
        Roll the appropriate die for loot based on ship size.
        
        Args:
            ship_size (str): The size of the ship ('small', 'medium', or 'treasure')
            
        Returns:
            int: The result of the loot roll
        """
        die_size = {
            'small': 6,
            'medium': 8,
            'treasure': 10
        }.get(ship_size.lower(), 6)  # Default to d6 if size is invalid
        
        return random.randint(1, die_size)

class PlayerCharacterCreation(GameMasterAgent):
    def __init__(self, name: str, origin_story: str):
        """
        Initialize the PlayerCharacterCreation agent.
        
        Args:
            name (str): The character's name
            origin_story (str): The character's backstory
        """
        super().__init__()
        self.name = name
        self.origin_story = origin_story
        
    def generate_signature_loot(self) -> str:
        """
        Generate a signature piece of loot using the LLM based on the character's story.
            
        Returns:
            str: The generated signature loot
        """
        loot_prompt = f"""
        Create a humorous and thematic signature piece of loot for this goblin pirate:
        
        Name: {self.name}
        Origin Story: {self.origin_story}
        
        Create a unique piece of loot that:
        1. Fits the character's backstory and personality
        2. Has a humorous or interesting effect
        3. Is thematic to the goblin pirate setting
        4. Is described in 1-2 sentences
        
        Provide only the loot description, no additional commentary.
        """
        
        return self.call_llm(loot_prompt)
    
    def parse_llm_response(self, response: str) -> str:
        """
        Simple pass-through implementation of the abstract method.
        PlayerCharacterCreation uses raw text responses for loot generation.
        
        Args:
            response (str): The LLM's response
            
        Returns:
            str: The unchanged response
        """
        return response

class NarrativeAgent(GameMasterAgent):
    def __init__(self, character_stories: list[str], ship_story: str, deep_research: bool = False, max_iterations: int = 3):
        """
        Initialize the NarrativeAgent with character stories and ship story.
        
        Args:
            character_stories (list[str]): List of character backstories
            ship_story (str): The ship's story
            deep_research (bool): Whether to use iterative refinement for responses
            max_iterations (int): Maximum number of refinement iterations
        """
        super().__init__(deep_research=deep_research, max_iterations=max_iterations)
        self.character_stories = "-----\n------".join(character_stories)
        self.ship_story = ship_story
        self.current_story = ""
        self.full_story = ""
        self.end_stage = ""
        self.story_update_counter = 0
        self.max_updates_before_summary = 3
    
    def parse_llm_response(self, response: str) -> str:
        """
        Simple pass-through implementation of the abstract method.
        NarrativeAgent uses raw text responses and doesn't need structured parsing.
        
        Args:
            response (str): The LLM's response
            
        Returns:
            str: The unchanged response
        """
        return response

    def create_initial_narrative(self) -> str:
        """
        Create an initial game scenario using the LLM.
        
        Returns:
            str: The initial narrative setting up the game
        """
        initial_prompt = f"""
        Create an exciting and humorous opening narrative for a goblin pirate adventure:
        
        Goblin Characters: {self.character_stories}
        Ship Story: {self.ship_story}
        
        Create a narrative that:
        1. Sets up an interesting and challenging goal for the goblins
        2. Establishes the setting and atmosphere
        3. Introduces any important NPCs or factions
        4. Creates a sense of urgency or excitement
        5. Maintains the goblin pirate theme's humor
        
        The narrative should be about 2-3 paragraphs long and give the players a clear direction to pursue.
        
        Provide only the narrative, no additional commentary.
        """
        
        self.current_story = self.call_llm(initial_prompt)
        self.create_end_stage()
        return self.current_story
    
    def get_current_story_context(self) -> str:
        """Helper to retrieve the current memory buffer summary."""
        return "\n".join(self.memory)

    def create_end_stage(self) -> str:
        """
        Create a secret end stage narrative that will serve as the game's conclusion.
        
        Returns:
            str: The end stage narrative (not shown to players)
        """
        end_stage_prompt = f"""
        Create a brief, secret end stage narrative for this goblin pirate adventure:
        
        Goblin Characters: The crew of goblins.
        Ship Story: A tale of the goblin ship.
        Current Story Context: {self.get_current_story_context()}
        
        Create a narrative that:
        1. Describes a satisfying conclusion to the goblins' journey
        2. Ties together the characters' stories and the ship's story
        3. Includes a final challenge or reward
        4. Is about 2-3 sentences long
        5. Maintains the goblin pirate theme's humor
        
        This will be used to determine when the game should end, but players won't see it.
        
        Provide only the end stage narrative, no additional commentary.
        """
        
        self.end_stage = self.call_llm(end_stage_prompt)
        return self.end_stage

    def game_should_end(self) -> bool:
        """
        Determine if the current narrative has reached a satisfying conclusion.
        
        Returns:
            bool: True if the game should end, False otherwise
        """
        end_check_prompt = f"""
        Based on the following information, determine if the goblin pirate adventure has reached a satisfying conclusion:
        
        Current Story Context: {self.get_current_story_context()}
        Intended End Stage: {self.end_stage}
        
        Consider:
        1. Has the main goal been achieved?
        2. Have the characters' stories been resolved?
        3. Is there a natural stopping point?
        4. Would continuing feel forced or anti-climactic?
        
        Respond with ONLY "YES" or "NO", nothing else.
        """
        
        response = self.call_llm(end_check_prompt).strip().upper()
        return response == "YES"

    def append_to_story(self, new_content: str):
        """
        Append new external content to the story memory manually.
        """
        self.memory.append(f"Event: {new_content}")

class CombatAgent(GameMasterAgent):
    """Base class for combat agents to consolidate logic."""
    def summarize_raid(self) -> str:
        """Create a concise summary of the raid phase using the LLM and the memory buffer."""
        summary_prompt = f"""
        Create a concise and humorous summary of this goblin pirate raid:
        
        Full Raid Narrative Context:
        {"\n".join(self.memory)}
        
        Create a summary that:
        1. Captures the key events and turning points
        2. Highlights the most memorable character actions
        3. Includes the final outcome
        4. Maintains the goblin pirate theme's humor
        5. Is about 2-3 paragraphs long
        
        Focus on the most exciting and funny moments, and make it feel like a pirate's tale being retold in a tavern!
        """
        
        try:
            return self.call_llm(summary_prompt)
        except Exception as e:
            print(f"Error summarizing raid: {e}")
            return "The raid was a wild adventure, but the details are a bit fuzzy after all that grog!"

class TargetShipSchema(BaseModel):
    narrative: str = Field(description="The descriptive narrative of the target ship")
    difficulty: int = Field(description="The difficulty scale of the target ship from 2 to 12")
    
class BuildTargetShipAgent(GameMasterAgent):
    def __init__(self, deep_research: bool = False, max_iterations: int = 3):
        super().__init__(deep_research=deep_research, max_iterations=max_iterations)
        # Create a specialized structured chain specifically for this agent
        self.structured_chain = (
            self.prompt_template
            | self.client.with_structured_output(TargetShipSchema, method="function_calling")
        ).with_retry(stop_after_attempt=3)
    
    def parse_llm_response(self, response: str) -> str:
        """
        Simple pass-through implementation of the abstract method.
        BuildTargetShipAgent uses raw text responses and doesn't need structured parsing.
        
        Args:
            response (str): The LLM's response
            
        Returns:
            str: The unchanged response
        """
        return response

    def generate_target_ship(self, difficulty_hint: int, current_narrative: str) -> TargetShip:
        """
        Generate an enemy ship based on difficulty and current story context.
        
        Args:
            ship_difficulty (int): The difficulty rating of the ship (2-12)
            current_narrative (str): The current story context
            
        Returns:
            TargetShip: A new target ship with appropriate narrative and stats
        """
        # Generate narrative prompt
        narrative_prompt = f"""
        Create a humorous and exciting description of an enemy ship that the goblins have spotted:
        
        Suggested Difficulty Hint: {difficulty_hint} out of a maximum of 12
        Current Story Context: {current_narrative}
        
        Create a target ship that:
        1. Describes the ship's appearance and characteristics in the narrative field
        2. Hints at what kind of cargo or treasure it might carry
        3. Sets a firm difficulty scale between 2 and 12 in the difficulty field based on how impressive it is
        4. Maintains the goblin pirate theme's humor
        """
        
        try:
            # Get structured data from LLM
            ship_data = self.structured_chain.invoke({"prompt": narrative_prompt})
            
            # Create and return the TargetShip using the structured output
            return TargetShip(ship_data.difficulty, ship_data.narrative)
        except Exception as e:
            print(f"Error generating target ship: {e}")
            # Fallback
            return TargetShip(difficulty_hint, "A mysterious ship emerges from the fog!")

class ShipCombatAgent(CombatAgent):
    def __init__(self, deep_research: bool = False, max_iterations: int = 3):
        super().__init__(deep_research=deep_research, max_iterations=max_iterations)
    
    def parse_llm_response(self, response: str) -> str:
        """
        Simple pass-through implementation of the abstract method.
        ShipCombatAgent uses raw text responses and doesn't need structured parsing.
        
        Args:
            response (str): The LLM's response
            
        Returns:
            str: The unchanged response
        """
        return response
        
    def resolve_combat(self, attacking_ship: GoblinShip, target_ship: TargetShip, dice_agent: DiceAgent, player: PlayerCharacter, player_action: str):
        """
        Resolve a round of ship-to-ship combat.
        
        Args:
            attacking_ship: The goblin ship
            target_ship: The target ship
            dice_agent: Agent for rolling dice
            player: The player character taking the action
            player_action: Description of what the player is trying to do
            
        Returns:
            tuple[str, bool]: (combat narrative, whether target is now boardable)
        """
        target_escaped = False
        # Roll for attack
        difficulty_scaler = int(target_ship.difficulty//4)
        attack_roll = dice_agent.roll_2d6() + attacking_ship.cannons
        defense_roll = dice_agent.roll_2d6() + difficulty_scaler
        if defense_roll >= 12 + difficulty_scaler:
            target_escaped = True
        # Generate narrative prompt
        narrative_prompt = f"""
        Create a humorous and exciting narrative for this ship combat action:
        
        Goblin: {player.name}
        Character Story: {player.origin_story}
        Signature Loot: {player.signature_loot}
        Ship: {attacking_ship.name}
        Ship Story: {attacking_ship.get_summary()}
        Target Escaped: {target_escaped}
        
        Player's Action: {player_action}
        Attack Roll: {attack_roll} (including {attacking_ship.cannons} from ship's cannons)
        Defense Roll: {defense_roll} (including {target_ship.difficulty} from target's difficulty)
        
        Target Ship: {target_ship.narrative}
        Current Target Hull: {target_ship.hull}
        
        Create a narrative that may:
        1. Incorporates the player's specific action
        2. References their character's story and signature loot (if applicable and humorous)
        3. Describes the ship's role in the action
        4. Explains the outcome based on the rolls
        5. Maintains the goblin pirate theme's humor

        If and only if the target ship has escaped, add a humorous note about the target ship escaping.
        
        Provide only the narrative, no additional commentary. Think carefully about the narrative before responding, 
        and if a piece of information is not relevant to the action, don't include it. Here is what has happened so far:
        {"\n".join(self.memory)}
        """
        
        # Get narrative from LLM
        narrative = self.call_llm(narrative_prompt)
        if target_escaped:
            target_ship.escaped = True
            return narrative, False
        bonus = random.choice([0, 1, 2])
        # Calculate damage and determine if ship is boardable
        if attack_roll >= 12:
            damage = 3
        elif attack_roll > defense_roll:
            damage = attack_roll - defense_roll
        else:
            damage = 0
        
        # Apply damage
        target_ship.hull -= damage + bonus
        
        # Check if ship is now boardable
        is_boardable = target_ship.hull <= 5
        if is_boardable:
            target_ship.boardable = True
            narrative += f"\nThe {target_ship.narrative} is now vulnerable to boarding!"
        
        # Push event to memory
        self.memory.append(f"Combat Action ({player_action}): {narrative}")
        return

    def generate_loot_narrative(self, total_loot: int, ship_size: str, character_stories: list[str]) -> str:
        """
        Generate a humorous narrative for the loot collection phase.
        
        Args:
            total_loot (int): The total amount of loot collected
            ship_size (str): The size of the ship ('small', 'medium', or 'treasure')
            character_stories (list[str]): List of goblin character stories
            
        Returns:
            str: A humorous narrative describing the loot collection
        """
        loot_prompt = f"""
        Create a humorous narrative for the goblins collecting loot from the defeated ship:
        
        Total Loot Collected: {total_loot}
        Ship Size: {ship_size.title()} Ship
        Goblin Stories: {character_stories}
        
        Make it funny and describe how each goblin contributes to the looting process!
        """
        
        return self.call_llm(loot_prompt)

class BoardingCombatAgent(CombatAgent):
    def __init__(self, character_stories: list[str], ship_story: str, deep_research: bool = False, max_iterations: int = 3):
        super().__init__(deep_research=deep_research, max_iterations=max_iterations)
        self.character_stories = character_stories
        self.ship_story = ship_story

    def parse_llm_response(self, response: str) -> str:
        """
        Simple pass-through implementation of the abstract method.
        BoardingCombatAgent uses raw text responses and doesn't need structured parsing.
        
        Args:
            response (str): The LLM's response
            
        Returns:
            str: The unchanged response
        """
        return response
        
    def describe_boarding(self, pc_story_narrative: str, attacking_ship: GoblinShip, target_ship: TargetShip) -> str:
        """Describe the boarding action setup."""
        prompt = f"""
        Create an exciting and humorous narrative for the goblins boarding the enemy ship:
        
        Target Ship: {target_ship.narrative}
        Goblin Ship: {attacking_ship.name}
        Ship Story: {self.ship_story}
        
        Goblin Stories: {pc_story_narrative}
        
        Make it dramatic and funny, incorporating the goblins' personalities and the ships' characteristics!
        """
        return self.call_llm(prompt)
    
    def resolve_boarding_combat(self, goblin: PlayerCharacter, target_ship: TargetShip, dice_agent: DiceAgent, player_action: str) -> None:
        """
        Resolve a goblin's boarding combat action.
        
        Args:
            goblin: The attacking goblin
            target_ship: The target ship
            dice_agent: Agent for rolling dice
            player_action: Description of what the player is trying to do
            
        Returns:
            tuple[str, int]: (combat narrative, damage dealt)
        """
        # Determine which stat to use based on goblin's highest stat
        stats = {
            'strength': goblin.strength,
            'cunning': goblin.cunning,
            'marksmanship': goblin.marksmanship
        }
        best_stat = max(stats.items(), key=lambda x: x[1])
        
        # Roll for attack
        attack_roll = dice_agent.roll_2d6() + best_stat[1]
        difficulty = target_ship.difficulty
        defender_roll = dice_agent.roll_2d6() + (difficulty//4)

        # Calculate damage and check for death
        if defender_roll >= 12:
            damage = 0
            goblin.living = False  # Set living to False when defender rolls 12+
        elif attack_roll >= difficulty:
            damage = attack_roll - difficulty
        else:
            damage = 0
        goblin_bonus = random.choice([0, 1, best_stat[1]])
        target_ship.hull -= damage + goblin_bonus
        
        # Generate narrative prompt
        narrative_prompt = f"""
        Create a humorous and exciting narrative for this boarding combat action:
        
        Goblin: {goblin.name}
        Character Story: {goblin.origin_story}
        Signature Loot: {goblin.signature_loot}
        Best Stat: {best_stat[0]} ({best_stat[1]})
        
        Player's Action: {player_action}
        Attack Roll: {attack_roll} (including {best_stat[1]} from {best_stat[0]})
        Defender Roll: {defender_roll} (including {difficulty//4} from target's difficulty)
        Difficulty: {difficulty}
        Damage to Target Ship: {damage}
        Did the attacking {goblin.name} survive? {goblin.living}
        
        Target Ship: {target_ship.narrative}
        
        Create a narrative that:
        1. Incorporates the player's specific action
        2. References their character's story and signature loot
        3. Explains how they use their best stat ({best_stat[0]})
        4. Describes the outcome based on the rolls
        5. Maintains the goblin pirate theme's humor
        
        Provide only the narrative, no additional commentary. Here is the running narrative so far, if any:
        {"\n".join(self.memory)}
        """
        
        # Get narrative from LLM
        narrative = self.call_llm(narrative_prompt)
        
        # Save context to memory
        self.memory.append(f"Boarding Action ({player_action}): {narrative}")
        return None