import da

from service_exception import ServiceException

class Manager:
    def __init__(self, username):
        self.user = da.get_user_by_username(username)

    def login(self, fb_user):
        # Check if they are registering or logging in
        if self.user is None:
            # They are registering a new account
            new_user = {
                "username": fb_user["email"],
                "name": fb_user["name"]
            }
            return da.create_user(new_user)
        else:
            # They are logging in. Return the user attached to their authentication token
            return self.user

    def get_tournaments(self):
        return da.get_tournaments()

    def create_tournament(self, tournament):
        # Check for a tournament
        if tournament is None:
            raise ServiceException("No tournament passed in to create", 400)
        # Check if user is an admin
        if self.user["admin"] == 0:
            raise ServiceException("You do not have permission to create a tournament", 403)
        return da.create_tournament(tournament)

    def get_brackets(self, tournament_id):
        return da.get_brackets(tournament_id)

    def create_bracket(self, tournament_id, bracket):
        if bracket is None:
            raise ServiceException("Invalid bracket passed in", 400)

        # Check that the tournament exists
        tournament = da.get_tournament(tournament_id)
        if tournament is None:
            raise ServiceException("This tournament does not exist.", 400)

        # Check master bracket exists
        if tournament["master_bracket_id"] is None:
            # If the user is not an admin do not allow them to create the master
            if self.user["admin"] == 0:
                raise ServiceException("You do not have permission to create this bracket", 403)

            # TODO: Think about auto generating empty matches

            # If user is an admin allow them to create the master bracket
            bracket_to_create = {"tournament_id": tournament["tournament_id"], "name": tournament["name"] + " - Results"}
            new_bracket_id = self.create_and_fill_bracket(bracket_to_create, bracket)
            tournament["master_bracket_id"] = new_bracket_id
            da.update_tournament(tournament["tournament_id"], tournament)
            return self.get_bracket(new_bracket_id)

        # See if the user already has a bracket
        if da.get_bracket(tournament_id = tournament_id, user_id = self.user["user_id"]) is not None:
            raise ServiceException("You have already created a bracket", 412)

        # create the users bracket
        bracket_to_create = {"user_id": self.user["user_id"], "tournament_id": tournament["tournament_id"], "name": bracket["name"]}
        master = self.get_bracket(tournament["master_bracket_id"])
        new_bracket_id = self.create_and_fill_bracket(bracket_to_create, master)
        return self.get_bracket(new_bracket_id)

    def create_bracket_and_matches(self, bracket):
        new_bracket_id = da.create_bracket(bracket)["bracket_id"]
        da.create_matches(new_bracket_id, bracket["rounds"])

    def update_bracket(self, bracket_id, bracket):
        if bracket is None or bracket["name"] is None or bracket["rounds"] is None:
            raise ServiceException("Invalid bracket passed in", 400)

        original_bracket = self.get_bracket(bracket_id)
        original_bracket["name"] = bracket["name"]
        
        original_rounds, rounds = original_bracket["rounds"], bracket["rounds"]
        if len(original_rounds) != len(rounds):
            raise ServiceException("Invalid bracket size passed in. {} != {}".format(len(original_rounds), len(rounds)), 400)

        for original_round, round in zip(original_rounds, rounds):
            if len(original_round) != len(round):
                raise ServiceException("Invalid round size passed in. {} != {}".format(len(original_round), len(round)), 400)

            for original_match, match in zip(original_round, round):
                # Only update the matches that have changed
                if original_match["player1_id"] != match.get("player1_id") or original_match["player2_id"] != match.get("player2_id") or original_match["winner_id"] != match.get("winner_id"):
                    original_match["player1_id"] = match.get("player1_id")
                    original_match["player2_id"] = match.get("player2_id")
                    original_match["seed1"] = match.get("seed1")
                    original_match["seed2"] = match.get("seed2")
                    original_match["winner_id"] = match.get("winner_id")
                    da.update_match(original_match["match_id"], original_match)

        da.update_bracket(bracket_id, original_bracket)
        return self.get_bracket(bracket_id)

    def get_my_bracket(self, tournament_id):
        bracket = da.get_bracket(tournament_id = tournament_id, user_id = self.user["user_id"])
        if bracket is None:
            raise ServiceException("No bracket existed for user_id: {} in tournament_id: {}".format(tournament_id, self.user["user_id"]), 404)
        bracket["rounds"] = self.get_rounds(bracket["bracket_id"])
        return bracket

    def get_bracket(self, bracket_id):
        bracket = da.get_bracket(bracket_id)
        if bracket is None:
            raise ServiceException("This bracket does not exist", 400)
        bracket["rounds"] = self.get_rounds(bracket_id)
        return bracket

    @staticmethod
    def get_rounds(bracket_id):
        matches = da.get_matches(bracket_id)
        rounds = []
        curr_round = 0
        for match in matches:
            round = match["round"]
            if round == curr_round + 1:
                curr_round = round
                rounds.append([])

            # This means that the rounds did not go sequentially (1, 2, 3...). One was missing...
            if round != curr_round:
                raise ServiceException("The matches for this tournament are corrupted. The bracket will need to be reset.")

            # The -1 is because rounds are one indexed and arrays are zero indexed
            rounds[curr_round - 1].append(match)
        return rounds

    @staticmethod
    def create_and_fill_bracket(bracket_to_create, bracket_to_copy):
        if "rounds" not in bracket_to_copy:
            raise ServiceException("Cannot copy a bracket with no rounds", 400)
        new_bracket = da.create_bracket(bracket_to_create)
        for rounds in bracket_to_copy["rounds"]:
            for match in rounds:
                match["bracket_id"] = new_bracket["bracket_id"]
                da.create_match(match)
        return new_bracket["bracket_id"]
