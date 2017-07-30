import da

class Manager:
    def __init__(self):
        pass

    ### USERS ###

    def get_users(self):
        return da.get_users()

    def get_user(self, user_id):
        return da.get_user(user_id)

    def create_user(self, user):
        return da.create_user(user)

    def update_user(self, user_id, user):
        return da.update_user(user_id, user)

    def delete_user(self, user_id):
        return da.delete_user(user_id)

    ### PLAYERS ###

    def get_players(self):
        return da.get_players()

    def get_player(self, player_id):
        return da.get_player(player_id)

    def create_player(self, player):
        return da.create_player(player)

    def update_player(self, player_id, player):
        return da.update_player(player_id, player)

    def delete_player(self, player_id):
        return da.delete_player(player_id)

    ### TOURNAMENTS ###

    def get_tournaments(self):
        return da.get_tournaments()

    def get_tournament(self, tournament_id):
        return da.get_tournament(tournament_id)

    def create_tournament(self, tournament):
        return da.create_tournament(tournament)

    def update_tournament(self, tournament_id, tournament):
        return da.update_tournament(tournament_id, tournament)

    def delete_tournament(self, tournament_id):
        return da.delete_tournament(tournament_id)

    ### BRACKETS ###

    def get_brackets(self):
        return da.get_brackets()

    def get_bracket(self, bracket_id):
        return da.get_bracket(bracket_id)

    def create_bracket(self, bracket):
        return da.create_bracket(bracket)

    def update_bracket(self, bracket_id, bracket):
        return da.update_bracket(bracket_id, bracket)

    def delete_bracket(self, bracket_id):
        return da.delete_bracket(bracket_id)

    ### MATCHES ###

    def get_matches(self):
        return da.get_matches()

    def get_match(self, match_id):
        return da.get_match(match_id)

    def create_match(self, match):
        return da.create_match(match)

    def update_match(self, match_id, match):
        return da.update_match(match_id, match)

    def delete_match(self, match_id):
        return da.delete_match(match_id)
