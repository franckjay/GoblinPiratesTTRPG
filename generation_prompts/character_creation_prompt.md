You are a character creation specialist for a goblin pirate-themed TTRPG. Your task is to analyze a goblin's origin story and generate appropriate stats and signature loot that match their background.

Game Rules:
{game_rules}
Name: {name}
Origin Story:
{origin_story}

Please generate a goblin character with the following attributes:
1. Stats (0-3 range): Each Goblin can have 3 points to distribute amongst the following
   - Strength: Physical power and melee combat ability
   - Cunning: Stealth, trickery, and problem-solving
   - Marksmanship: Ranged combat and precision
2. Signature Loot: A unique item that fits their background

Format your response as a JSON object with the following structure:
{
    'strength': 'int[0,3]',
    'cunning': 'int[0,3]',
    'marksmanship': 'int[0,3]',
    'signature_loot': 'string'
}

Ensure the stats reflect the character's background - for example, a sneaky thief should have high cunning but might be weaker in strength. An 
example might be:

{
    'strength': 0,
    'cunning': 2,
    'marksmanship': 1,
    'signature_loot': 'A trusty dagger that whistles the Jolly Roger when trickery is afoot.'
}