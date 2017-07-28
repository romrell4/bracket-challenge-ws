class Bracket:
    def __init__(self, data):
        [self.bracket_id, self.user_id, self.tournament_id, self.name] = data

    def to_dict(self):
        return {
            "bracket_id": self.bracket_id,
            "user_id": self.user_id,
            "tournament_id": self.tournament_id,
            "name": self.name
        }