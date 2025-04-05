import random
from .models import PlayerCharacter, GoblinShip
from .agents import PlayerCharacterCreation, NarrativeAgent, DiceAgent, ShipCombatAgent, BoardingCombatAgent, BuildTargetShipAgent

NO_RAID_STR = "No target ship spotted."

def player_action_promt(pc: PlayerCharacter):
            print(f"\n{pc.name}'s turn!")
            print("Available actions:")
            print("1. Spy a Target (Roll 2d6)")
            print("2. Repair the Ship (Cost: 10 Loot)")
            print("3. Train the Crew (Cost: 5 Loot to Improve Morale)")
            print("4. Upgrade the Ship (Cost: 20 Loot)")
            print("5. Do nothing! (Free)")
            
def print_upgrade_options():
    print("\nAvailable upgrades:")
    print("1. Hull")
    print("2. Speed")
    print("3. Cannons")
    print("4. Trickery")

def create_player_character(player_number: int = None) -> PlayerCharacter:
    """
    Create a new player character.
    
    Args:
        player_number (int, optional): The player number for the prompt. If None, no number will be shown.
        
    Returns:
        PlayerCharacter: The newly created character
    """
    name_prompt = f"Enter name for Goblin {player_number + 1}: " if player_number is not None else "Enter name for your new Goblin: "
    name = input(name_prompt)
    story = input(f"Write a short backstory for {name}: ")
    
    # Generate signature loot using the LLM
    character_creator = PlayerCharacterCreation(name, story)
    signature_loot = character_creator.generate_signature_loot()
    print(f"\nYour signature loot: {signature_loot}")
    
    # Let the user allocate stats
    print("\nYou have 3 points to allocate between Strength, Cunning, and Marksmanship.")
    print("Each stat can be between 0 and 3, and the total must be 3.")
    attribute_bank = 3
    strength = cunning = marksmanship = 0
    while attribute_bank > 0:
        print(f"You have {attribute_bank} points left to allocate.")
        choice = input("Enter the stat you want to allocate to: (1) Strength, (2) Cunning, (3) Marksmanship: ")
        if choice == "1":
            strength += 1
        elif choice == "2":
            cunning += 1
        elif choice == "3":
            marksmanship += 1
        else:
            print("Invalid choice! Please try again.")
            attribute_bank += 1
        attribute_bank -= 1

    return PlayerCharacter(
        name=name,
        origin_story=story,
        strength=strength,
        cunning=cunning,
        marksmanship=marksmanship,
        signature_loot=signature_loot
    )

def main():
    num_players = int(input("Enter number of players: "))
    player_characters = []
    dice_agent = DiceAgent()
    
    for i in range(num_players):
        character = create_player_character(i)
        player_characters.append(character)
    
    ship_name = input("Enter name for your goblin ship: ")
    goblin_ship = GoblinShip(ship_name)
    ship_story = input("Argghhhh! What's our ship story?: ")
    # TODO: optionally create the ship story via Agent
    # goblin_ship.create_initial_ship_story(ship_story)
    goblin_ship.ship_story = ship_story
    
    # Generate the game scenario
    narrative_agent = NarrativeAgent(
        [pc.origin_story for pc in player_characters],
        goblin_ship.ship_story
    )
    
    # Create initial narrative and end stage
    initial_narrative = narrative_agent.create_initial_narrative()
    print("\n" + initial_narrative)
    narrative_agent.create_end_stage()  # Create but don't show the end stage
    
    # Initialize the BuildTargetShipAgent
    target_ship_agent = BuildTargetShipAgent()
    
    game_ongoing = True
    
    while game_ongoing:
        print("\n--- Sail Phase! ---")
        
        # Randomize player order for this phase
        current_players = player_characters.copy()
        random.shuffle(current_players)
        target_ship = None
        # Each player takes their turn
        for player in current_players:
            player_action_promt(player)
            
            action = input(f"What would you like to do, {player.name} with your total loot at {goblin_ship.loot}? (1-5): ")
            
            if action == "1":
                roll = dice_agent.roll_2d6()
                print(f"You rolled a {roll}!")
                if roll >= 10:
                    print("You found an especially rich target!")
                    ship_difficulty = random.randint(8, 12)
                elif roll >= 7:
                    print("You found an average ship.")
                    ship_difficulty = random.randint(5, 7)
                else:
                    print("You found a weak ship... or is it an ambush?")
                    ship_difficulty = random.choice([2, 3, 4, 12])
                
                # Generate target ship using the BuildTargetShipAgent
                target_ship = target_ship_agent.generate_target_ship(
                    ship_difficulty,
                    narrative_agent.current_story
                )
                print(f"\nTarget Ship Details:\n{target_ship.get_summary()}")
            
            elif action == "2":
                if goblin_ship.repair():
                    print(f"\nShip repaired! Current stats:\n{goblin_ship.get_summary()}")
                else:
                    print("Not enough loot! Need 10 loot to repair.")
            
            elif action == "3":
                if goblin_ship.train_crew():
                    print(f"\nCrew trained! Current stats:\n{goblin_ship.get_summary()}")
                else:
                    print("Not enough loot! Need 5 loot to train crew.")
            
            elif action == "4":
                print_upgrade_options()
                upgrade_choice = input("Which stat would you like to upgrade? (1-4): ")
                stat_map = {
                    "1": "hull",
                    "2": "speed",
                    "3": "cannons",
                    "4": "trickery"
                }
                if upgrade_choice in stat_map:
                    if goblin_ship.upgrade(stat_map[upgrade_choice]):
                        print(f"\nShip upgraded! Current stats:\n{goblin_ship.get_summary()}")
                    else:
                        print("Not enough loot! Need 20 loot to upgrade.")
                else:
                    print("Invalid upgrade choice!")
            
            else:
                print("No action!")
        
        print("\n--- Raid Phase! ---")
        should_loot = False
        if target_ship:
            print(f"Target ship spotted: {target_ship.narrative} (Difficulty {target_ship.difficulty})")
            
            # Initialize combat agents
            ship_combat_agent = ShipCombatAgent()
            boarding_agent = BoardingCombatAgent(
                [pc.origin_story for pc in player_characters],
                goblin_ship.ship_story
            )
            
            # Ship-to-ship combat phase
            print("\n--- Ship-to-Ship Combat! ---")
            while not target_ship.boardable and not target_ship.escaped:
                # Each player takes a turn in ship combat
                for player in current_players:
                    print(f"\n{player.name}'s turn in ship combat!")
                    print(f"Current ship stats:\n{goblin_ship.get_summary()}")
                    print(f"Target ship status:\n{target_ship.get_summary()}")
                    
                    # Get player's action description
                    player_action = input(f"What would you like to do with the ship, {player.name}? ")
                    
                    # Resolve combat
                    ship_combat_agent.resolve_combat(
                        goblin_ship,
                        target_ship,
                        dice_agent,
                        player,
                        player_action
                    )
                    print(f"\nTarget ship hull: {target_ship.hull}")
                    # Check if ship is now boardable
                    if target_ship.boardable:
                        break
                    # Check if ship escaped (12+ on defense roll)
                    if target_ship.escaped is True:
                        should_loot = False
                        break
            
            # Boarding combat phase
            while target_ship.boardable and not target_ship.escaped and target_ship.hull > 0:
                print("\n--- Boarding Combat! ---")
                # Describe the boarding action
                boarding_agent.describe_boarding(
                    [pc.origin_story for pc in player_characters],
                    goblin_ship,
                    target_ship
                )

                # Each player takes a turn in boarding combat
                for player_idx in range(len(current_players)):
                    player = current_players[player_idx]
                    print(f"\n{player.name}'s turn in boarding combat!")
                    print(f"Your stats:\n{player.get_summary()}")
                    print(f"Target ship status:\n{target_ship.get_summary()}")
                    
                    # Get player's action description
                    player_action = input(f"What would you like to do, {player.name}? ")
                    
                    # Resolve boarding combat
                    boarding_agent.resolve_boarding_combat(
                        player,
                        target_ship,
                        dice_agent,
                        player_action
                    )

                    if not player.living:
                        print(f"\n{player.name} has fallen in battle! Time for a new goblin to join the crew!")
                        player = create_player_character()
                        current_players[player_idx] = player
                        player_characters[player_idx] = player  # Update the main list as well
                        print(f"Welcome {player.name} to the crew!")
                    print(f"Target crew is down to  {target_ship.hull}!")
            
            # Check combat results
            if target_ship.escaped:
                raid_outcome = "The enemy ship managed to escape!"
                should_loot = False
            elif target_ship.hull <= 0:
                raid_outcome = "The enemy ship has been defeated!"
                should_loot = True
            else:
                raid_outcome = "The battle continues..."
                should_loot = False

        else:
            raid_outcome = NO_RAID_STR
        # End of the Rqaid    
        print(raid_outcome)
        if target_ship and ship_combat_agent.running_narrative:
            raid_narrative = ship_combat_agent.summarize_raid() 
            # Append the raid narrative to the NarrativeAgent. This also summarizes the story.
            narrative_agent.append_to_story(raid_narrative)
            # If there was boarding, summarize it and append it to the story.
        if boarding_agent.running_narrative:
            boarding_agent.running_narrative+= "\n" + raid_outcome
            raid_narrative = boarding_agent.summarize_raid()
            narrative_agent.append_to_story(raid_narrative)

        print("\n--- Loot Phase! ---")
        if should_loot is True:
            # Determine ship size based on ship stats
            total_stats = goblin_ship.speed + goblin_ship.cannons + goblin_ship.trickery
            if total_stats <= 3:
                ship_size = 'small'
            elif total_stats <= 9:
                ship_size = 'medium'
            else:
                ship_size = 'treasure'
            
            print(f"\nYour ship's total stats: {total_stats}")
            print(f"Rolling for loot with a {ship_size} ship...")
            
            # Each player rolls for loot
            total_loot = 0
            for player in current_players:
                loot_roll = dice_agent.roll_loot_die(ship_size)
                total_loot += loot_roll
                print(f"{player.name} rolled a {loot_roll}!")
            
            # Add loot to the ship
            goblin_ship.loot += total_loot
            print(f"\nTotal loot collected: {total_loot}")
            print(f"Current ship loot: {goblin_ship.loot}")
            
            # Generate loot narrative using the ShipCombatAgent
            loot_narrative = ship_combat_agent.generate_loot_narrative(
                total_loot,
                ship_size,
                [pc.origin_story for pc in player_characters]
            )
            print("\n" + loot_narrative)
            
            # Append loot narrative to the story
            narrative_agent.append_to_story(loot_narrative)

        # Check if the game should end based on narrative progression
        if narrative_agent.game_should_end():
            print("\nThe goblins feel like they're approaching a natural conclusion to their adventure...")
            optional_game_ongoing = input("Would you like to end the game here? (y/n): ").lower() == 'y'
            if optional_game_ongoing:
                game_ongoing = False
        else:
            optional_game_ongoing = input("Continue playing the game? (y/n): ").lower() == 'y'
            if not optional_game_ongoing:
                game_ongoing = False
        
        if not game_ongoing:
            print("\nGame Over! Thanks for playing!")

if __name__ == "__main__":
    main()
