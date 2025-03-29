class PlayerCharacter:
    def __init__(self, name: str, origin_story: str, strength: int, cunning: int, marksmanship: int, signature_loot: str):
        self.name = name
        self.origin_story = origin_story
        self.strength = strength
        self.cunning = cunning
        self.marksmanship = marksmanship
        self.signature_loot = signature_loot
        self.living = True

    def get_summary(self):
        return f"Name: {self.name}\nOrigin Story: {self.origin_story}\nStrength: {self.strength}\nCunning: {self.cunning}\nMarksmanship: {self.marksmanship}\nSignature Loot: {self.signature_loot}"

class GoblinShip:
    def __init__(self, name):
        self.name = name
        self.hull = 20
        self.speed = 1
        self.cannons = 1
        self.trickery = 1
        self.loot = 0
        self.max_hull = 20

    def repair(self) -> bool:
        """
        Repair the ship's hull if enough loot is available.
        
        Returns:
            bool: True if repair was successful, False otherwise
        """
        if self.loot >= 10:
            self.loot -= 10
            self.hull = min(self.max_hull, self.hull + 5)
            return True
        return False

    def train_crew(self) -> bool:
        """
        Train the crew to improve ship stats.
        
        Returns:
            bool: True if training was successful, False otherwise
        """
        if self.loot >= 5:
            self.loot -= 5
            # Improve all stats slightly
            self.speed = min(5, self.speed + 1)
            self.cannons = min(5, self.cannons + 1)
            self.trickery = min(5, self.trickery + 1)
            return True
        return False

    def upgrade(self, stat: str) -> bool:
        """
        Upgrade a specific ship stat if enough loot is available.
        
        Args:
            stat (str): The stat to upgrade ('hull', 'speed', 'cannons', or 'trickery')
            
        Returns:
            bool: True if upgrade was successful, False otherwise
        """
        if self.loot < 20:
            return False
            
        if stat in ['hull', 'speed', 'cannons', 'trickery']:
            self.loot -= 20
            if stat == 'hull':
                self.max_hull += 5
                self.hull += 5
            else:
                setattr(self, stat, min(5, getattr(self, stat) + 1))
            return True
        return False

    def get_summary(self):
        return f"Ship Name: {self.name}\nHull: {self.hull}/{self.max_hull}\nSpeed: {self.speed}\nCannons: {self.cannons}\nTrickery: {self.trickery}\nLoot: {self.loot}"

class TargetShip:
    def __init__(self, difficulty, narrative):
        self.hull = max(5, difficulty)  # Hull scales with difficulty
        self.difficulty = difficulty
        self.narrative = narrative
        self.boardable = False
        self.escaped = False

    def get_summary(self):
        return f"Target Ship\nDifficulty: {self.difficulty}\nHull: {self.hull}\nBoardable: {self.boardable}\nEscaped: {self.escaped}" 