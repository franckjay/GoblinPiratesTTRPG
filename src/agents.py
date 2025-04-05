from abc import ABC, abstractmethod
import os

from openai import OpenAI
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
        self.full_story = self._create_full_story()
        self.create_end_stage()
        return self.current_story

    def create_end_stage(self) -> None:
        """
        Create a secret end stage narrative that will serve as the game's conclusion.
        
        Returns:
            str: The end stage narrative (not shown to players)
        """
        end_stage_prompt = f"""
        Create a brief, secret end stage narrative for this goblin pirate adventure:
        
        Goblin Characters: {self.character_stories}
        Ship Story: {self.ship_story}
        Current Story: {self.current_story}
        
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
        
        Current Story: {self.current_story}
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

    def _create_full_story(self):
        """Create the full story from the character, narrative, and ship stories"""
        return f"This is a hilarious and fun-filled story about these goblins {self.character_stories} and their ship, {self.ship_story}. This is the story thus far: {self.current_story}"

    def append_to_story(self, new_content: str):
        """
        Append new content to the story and update the full story.
        If enough updates have occurred, trigger a story summarization.
        
        Args:
            new_content (str): New story content to append
        """
        # Append the new content with a separator
        self.current_story += f"\n\n{new_content}"
        
        # Update the full story
        self.full_story = self._create_full_story()
        
        # Increment counter and check if we should summarize
        self.story_update_counter += 1
        if self.story_update_counter >= self.max_updates_before_summary:
            self._summarize_story()
            self.story_update_counter = 0  # Reset counter

    def _summarize_story(self):
        """
        Use the LLM to create a concise summary of the full story,
        preserving key narrative elements while reducing length.
        """
        summarization_prompt = f"""
        Please create a concise summary of this goblin pirate adventure story, 
        preserving the key narrative elements, character development, and important events.
        The goal of this summary should be to inform the Game Master what has happened so far in the story,
        and to preserve running jokes and gags.
        
        Original story:
        {self.full_story}
        
        Provide only the summarized story, with no additional commentary.
        """
        
        try:
            summarized_story = self.call_llm(summarization_prompt)
            self.current_story = summarized_story
            self.full_story = self._create_full_story()
        except Exception as e:
            print(f"Error during story summarization: {e}")
            # If summarization fails, continue with the original story
            pass

class BuildTargetShipAgent(GameMasterAgent):
    def __init__(self, deep_research: bool = False, max_iterations: int = 3):
        super().__init__(deep_research=deep_research, max_iterations=max_iterations)
    
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
        
    def generate_target_ship(self, ship_difficulty: int, current_narrative: str) -> TargetShip:
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
        
        Ship Difficulty: {ship_difficulty} out of a maximum of 12
        Current Story Context: {current_narrative}
        
        Create a narrative that:
        1. Describes the ship's appearance and characteristics
        2. Hints at what kind of cargo or treasure it might carry
        3. Includes some humorous or interesting details about the ship
        4. Fits the difficulty level (higher difficulty = more impressive ship)
        5. Maintains the goblin pirate theme's humor
        
        Provide only the ship description, no additional commentary.
        """
        
        # Get narrative from LLM
        narrative = self.call_llm(narrative_prompt)
        
        # Create and return the TargetShip
        return TargetShip(ship_difficulty, narrative)

class ShipCombatAgent(GameMasterAgent):
    def __init__(self, deep_research: bool = False, max_iterations: int = 3):
        super().__init__(deep_research=deep_research, max_iterations=max_iterations)
        self.running_narrative = ""
    
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
        
    def resolve_combat(self, attacking_ship: GoblinShip, target_ship: TargetShip, dice_agent: DiceAgent, player: PlayerCharacter, player_action: str) -> None:
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
        attack_roll = dice_agent.roll_2d6() + attacking_ship.cannons
        defense_roll = dice_agent.roll_2d6() + int(target_ship.difficulty//4)
        if defense_roll >= 12:
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
        {self.running_narrative}
        """
        
        # Get narrative from LLM
        narrative = self.call_llm(narrative_prompt)
        if target_escaped:
            target_ship.escaped = True
            return narrative, False
        
        # Calculate damage and determine if ship is boardable
        if attack_roll >= 12:
            damage = 3
        elif attack_roll > defense_roll:
            damage = attack_roll - defense_roll
        else:
            damage = 0
        
        # Apply damage
        target_ship.hull -= damage
        
        # Check if ship is now boardable
        is_boardable = target_ship.hull <= 5
        if is_boardable:
            target_ship.boardable = True
            narrative += f"\nThe {target_ship.narrative} is now vulnerable to boarding!"
        self.running_narrative += narrative
        print(narrative)
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

    def summarize_raid(self) -> str:
        """
        Create a concise summary of the raid phase using the LLM.
        
        Args:
            raid_narrative (str): The full narrative of the raid phase
            
        Returns:
            str: A concise summary of the raid phase
        """
        summary_prompt = f"""
        Create a concise and humorous summary of this goblin pirate raid:
        
        Full Raid Narrative:
        {self.running_narrative}
        
        Create a summary that:
        1. Captures the key events and turning points
        2. Highlights the most memorable character actions
        3. Includes the final outcome
        4. Maintains the goblin pirate theme's humor
        5. Is about 2-3 paragraphs long
        
        Focus on the most exciting and funny moments, and make it feel like a pirate's tale being retold in a tavern!
        
        Provide only the summary, no additional commentary.
        """
        
        try:
            return self.call_llm(summary_prompt)
        except Exception as e:
            print(f"Error summarizing raid: {e}")
            return "The raid was a wild adventure, but the details are a bit fuzzy after all that grog!"

class BoardingCombatAgent(GameMasterAgent):
    def __init__(self, character_stories: list[str], ship_story: str, deep_research: bool = False, max_iterations: int = 3):
        super().__init__(deep_research=deep_research, max_iterations=max_iterations)
        self.character_stories = character_stories
        self.ship_story = ship_story
        self.running_narrative = ""

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
            
        target_ship.hull -= damage
        
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
        {self.running_narrative}
        """
        
        # Get narrative from LLM
        narrative = self.call_llm(narrative_prompt)
        print(narrative)
        self.running_narrative += narrative
        return None
    
    def summarize_raid(self) -> str:
        """
        Create a concise summary of the raid phase using the LLM.
        
        Args:
            raid_narrative (str): The full narrative of the raid phase
            
        Returns:
            str: A concise summary of the raid phase
        """
        summary_prompt = f"""
        Create a concise and humorous summary of this goblin pirate raid:
        
        Full Raid Narrative:
        {self.running_narrative}
        
        Create a summary that:
        1. Captures the key events and turning points
        2. Highlights the most memorable character actions
        3. Includes the final outcome
        4. Maintains the goblin pirate theme's humor
        5. Is about 2-3 paragraphs long
        
        Focus on the most exciting and funny moments, and make it feel like a pirate's tale being retold in a tavern!
        
        Provide only the summary, no additional commentary.
        """
        
        try:
            return self.call_llm(summary_prompt)
        except Exception as e:
            print(f"Error summarizing raid: {e}")
            return "The raid was a wild adventure, but the details are a bit fuzzy after all that grog!"