json_format = """Format your response as a JSON object with the following structure:
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
    }"""