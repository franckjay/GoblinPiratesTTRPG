class PlayerCharacter:
    def __init__(self, name, origin_story, strength, cunning, marksmanship, signature_loot):
        self.name = name
        self.origin_story = origin_story
        self.strength = strength
        self.cunning = cunning
        self.marksmanship = marksmanship
        self.signature_loot = signature_loot

    def get_summary(self):
        return f"Name: {self.name}\nOrigin Story: {self.origin_story}\nStrength: {self.strength}\nCunning: {self.cunning}\nMarksmanship: {self.marksmanship}\nSignature Loot: {self.signature_loot}"

class GoblinShip:
    def __init__(self, name):
        self.name = name
        self.hull = 20
        self.speed = 1
        self.cannons = 1
        self.trickery = 1
    
    def get_summary(self):
        return f"Ship Name: {self.name}\nHull: {self.hull}\nSpeed: {self.speed}\nCannons: {self.cannons}\nTrickery: {self.trickery}"
    
    def upgrade(self, stat):
        if stat in ['hull', 'speed', 'cannons', 'trickery']:
            setattr(self, stat, getattr(self, stat) + 1)
        else:
            print("Invalid upgrade!")

class TargetShip:
    def __init__(self, difficulty, narrative):
        self.hull = max(5, difficulty * 3)  # Hull scales with difficulty
        self.difficulty = difficulty
        self.narrative = narrative
        self.boardable = False
        self.escaped = False

    def get_summary(self):
        return f"Target Ship\nDifficulty: {self.difficulty}\nHull: {self.hull}\nNarrative: {self.narrative}\nBoardable: {self.boardable}\nEscaped: {self.escaped}" 