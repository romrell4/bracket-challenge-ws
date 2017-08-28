class User:
    def __init__(self, result_set):
        [self.user_id, self.username, self.name, self.admin] = result_set

class Player:
    def __init__(self, result_set):
        [self.player_id, self.name] = result_set

class Tournament:
    def __init__(self, result_set):
        [self.tournament_id, self.name, self.master_bracket_id, self.image_url] = result_set

class Bracket:
    def __init__(self, result_set):
        [self.bracket_id, self.user_id, self.tournament_id, self.name] = result_set

class Match:
    def __init__(self, result_set):
        [self.match_id, self.bracket_id, self.round, self.position, self.player1_id, self.player2_id, self.seed1, self.seed2, self.winner_id] = result_set

class MatchHelper:
    def __init__(self, result_set):
        [self.match_id, self.bracket_id, self.round, self.position, self.player1_id, self.player1_name, self.player2_id, self.player2_name, self.seed1, self.seed2, self.winner_id, self.winner_name] = result_set

class Score:
    def __init__(self, result_set):
        [self.score] = result_set
