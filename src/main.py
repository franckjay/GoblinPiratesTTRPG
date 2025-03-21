import random
from .models import PlayerCharacter, GoblinShip, TargetShip
from .agents import PlayerCharacterCreation, NarrativeAgent

def main():
    num_players = int(input("Enter number of players: "))
    player_characters = []
    
    for i in range(num_players):
        name = input(f"Enter name for Goblin {i+1}: ")
        story = input(f"Write a short backstory for {name}: ")
        # Use the LLM agent to generate stats
        character = character_creator.generate_character(story)
        player_characters.append(character)
    
    ship_name = input("Enter name for your goblin ship: ")
    goblin_ship = GoblinShip(ship_name)
    
    # Generate the game scenario
    narrative_agent = NarrativeAgent()
    narrative = narrative_agent.create_initial_narrative([pc.origin_story for pc in player_characters])
    
    game_ongoing = True
    
    while game_ongoing:
        print("\n--- Sail Phase! ---")
        
        # Randomize player order for this phase
        current_players = player_characters.copy()
        random.shuffle(current_players)
        
        # Each player takes their turn
        for player in current_players:
            print(f"\n{player.name}'s turn!")
            print("Available actions:")
            print("1. Spy a Target (Roll 2d6)")
            print("2. Repair the Ship (Cost: 10 Loot)")
            print("3. Train the Crew (Improve Morale)")
            print("4. Upgrade the Ship (Cost: 20 Loot)")
            
            action = input(f"What would you like to do, {player.name}? (1-4): ")
            
            if action == "1":
                roll = random.randint(1, 6) + random.randint(1, 6)
                print(f"You rolled a {roll}!")
                if roll >= 10:
                    print("You found an especially rich target!")
                    ship_difficulty = random.randint(8, 12)
                elif roll >= 7:
                    print("You found an average ship.")
                    ship_difficulty = random.randint(5, 7)
                else:
                    print("You found a weak ship... or is it an ambush?")
                    ship_difficulty = random.randint(2, 4)
                
                target_narrative = "A mysterious enemy ship on the horizon..."
                target_ship = TargetShip(ship_difficulty, target_narrative)
                print(f"\nTarget Ship Details:\n{target_ship.get_summary()}")
            
            elif action == "2":
                # TODO: Implement repair logic
                print("Repair functionality coming soon!")
            
            elif action == "3":
                # TODO: Implement training logic
                print("Training functionality coming soon!")
            
            elif action == "4":
                print("\nAvailable upgrades:")
                print("1. Hull")
                print("2. Speed")
                print("3. Cannons")
                print("4. Trickery")
                upgrade_choice = input("Which stat would you like to upgrade? (1-4): ")
                stat_map = {
                    "1": "hull",
                    "2": "speed",
                    "3": "cannons",
                    "4": "trickery"
                }
                if upgrade_choice in stat_map:
                    goblin_ship.upgrade(stat_map[upgrade_choice])
                    print(f"\nShip upgraded! Current stats:\n{goblin_ship.get_summary()}")
                else:
                    print("Invalid upgrade choice!")
            
            else:
                print("Invalid action!")
        
        print("\n--- Raid Phase! ---")
        print(f"Target ship spotted: {target_ship.narrative} (Difficulty {target_ship.difficulty})")
        
        # Combat logic would go here, calling an LLM agent
        # Example placeholder:
        target_ship.hull -= 3  # Pretend the goblins did some damage
        if target_ship.hull <= 5:
            target_ship.boardable = True
        
        if target_ship.boardable:
            print("The target ship is now boardable!")
        else:
            print("The battle continues...")

        # TODO:
        
        # Example end condition:
        game_ongoing = input("Continue game? (y/n): ").lower() == 'y'
    
    print("Game Over!")

if __name__ == "__main__":
    main()
