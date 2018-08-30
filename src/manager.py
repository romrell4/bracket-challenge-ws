import scraper

from service_exception import ServiceException

class Manager:
    def __init__(self, da, username):
        self.da = da
        self.user = self.da.get_user_by_username(username)

    def login(self, fb_user):
        # Check if they are registering or logging in
        if self.user is None:
            # They are registering a new account
            new_user = {
                "username": fb_user["email"],
                "name": fb_user["name"]
            }
            return self.da.create_user(new_user)
        else:
            # They are logging in. Return the user attached to their authentication token
            return self.user

    def get_players(self):
        return self.da.get_players()

    def get_tournaments(self):
        return self.da.get_tournaments()

    def create_tournament(self, tournament):
        # Check for a tournament
        if tournament is None:
            raise ServiceException("No tournament passed in to create", 400)
        # Check if user is an admin
        if self.user["admin"] == 0:
            raise ServiceException("You do not have permission to create a tournament", 403)

        tournament["active"] = 1
        tournament = self.da.create_tournament(tournament)

        # If they set a draws_url, try to create the master bracket
        if tournament["draws_url"] is not None:
            self.scrape_master_bracket_draws(tournament["tournament_id"])
            return self.da.get_tournament(tournament["tournament_id"])
        else:
            return tournament

    def scrape_active_tournaments(self):
        if self.user.get("admin") != 1:
            raise ServiceException("You do not have permission to update master brackets", 403)

        tournaments = self.da.get_active_tournaments()
        for tournament in tournaments:
            print("Updating draws for {}".format(tournament.get("name")))
            self.scrape_master_bracket_draws(tournament.get("tournament_id"))

    def get_tournament(self, tournament_id):
        if tournament_id is None:
            raise ServiceException("Invalid parameters passed in", 400)
        return self.da.get_tournament(tournament_id)

    def update_tournament(self, tournament_id, tournament):
        # Check for valid parameters
        if tournament_id is None or tournament is None:
            raise ServiceException("Invalid parameters passed in", 400)
        # Make sure the user is an admin
        if self.user["admin"] == 0:
            raise ServiceException("You do not have permission to edit a tournament", 403)
        return self.da.update_tournament(tournament_id, tournament)

    def delete_tournament(self, tournament_id):
        if tournament_id is None or self.da.get_tournament(tournament_id) is None:
            raise ServiceException("Invalid tournament id passed in", 400)
        # Make sure the user is an admin
        if self.user["admin"] == 0:
            raise ServiceException("You do not have permission to delete a tournament", 403)
        self.da.delete_tournament(tournament_id)

    def scrape_master_bracket_draws(self, tournament_id):
        # Check for valid parameters
        tournament = self.da.get_tournament(tournament_id)
        if tournament is None:
            raise ServiceException("Invalid parameters passed in", 400)
        elif self.user.get("admin") != 1:
            raise ServiceException("You do not have permission to update draws", 403)
        elif tournament.get("draws_url") is None:
            raise ServiceException("The draws are not yet attached to this tournament. Unable to update", 412)

        scraped_bracket = scraper.scrape_bracket(tournament.get("draws_url"), self.da.get_players())

        if scraped_bracket is None:
            raise ServiceException("Unable to scrape bracket from {}".format(tournament.get("draws_url")), 400)

        master_bracket_id = tournament.get("master_bracket_id")
        if master_bracket_id is None:
            # Create the master bracket
            return self.create_bracket(tournament_id, scraped_bracket)
        else:
            # Update the master bracket (which will also update other brackets' first round)
            master_bracket = self.get_bracket(master_bracket_id)
            master_bracket["rounds"] = scraped_bracket["rounds"]
            return self.update_bracket(master_bracket_id, master_bracket)

    def get_brackets(self, tournament_id):
        return sorted([self.fill_bracket(bracket) for bracket in self.da.get_brackets(tournament_id)], key = lambda bracket: bracket["score"], reverse = True)

    def create_bracket(self, tournament_id, bracket):
        if bracket is None:
            raise ServiceException("Invalid bracket passed in", 400)

        # Check that the tournament exists
        tournament = self.da.get_tournament(tournament_id)
        if tournament is None:
            raise ServiceException("This tournament does not exist.", 400)

        # Check master bracket exists
        if tournament.get("master_bracket_id") is None:
            # If the user is not an admin do not allow them to create the master
            if self.user.get("admin") != 1:
                raise ServiceException("You do not have permission to create this bracket", 403)

            # Can't create a master bracket with no rounds
            if "rounds" not in bracket:
                raise ServiceException("Cannot create a master bracket with no rounds", 400)

            # Finds and creates new players
            self.create_new_players(bracket.get("rounds"))

            # creates the bracket and matches
            bracket_to_create = {"tournament_id": tournament_id, "name": tournament.get("name") + " - Results", "rounds": bracket.get("rounds")}
            new_bracket_id = self.create_bracket_and_matches(bracket_to_create)
            tournament["master_bracket_id"] = new_bracket_id
            self.da.update_tournament(tournament.get("tournament_id"), tournament)
            return self.get_bracket(new_bracket_id)

        # See if the user already has a bracket
        if self.da.get_bracket(tournament_id = tournament_id, user_id = self.user.get("user_id")) is not None:
            raise ServiceException("You have already created a bracket", 412)

        # create the users bracket
        master = self.get_bracket(tournament.get("master_bracket_id"))
        bracket_to_create = {"tournament_id": tournament_id, "name": bracket.get("name"), "user_id": self.user.get("user_id"), "rounds": master.get("rounds")}
        new_bracket_id = self.create_bracket_and_matches(bracket_to_create)
        return self.get_bracket(new_bracket_id)

    def update_bracket(self, bracket_id, bracket):
        # Validate the input
        if bracket is None or "name" not in bracket or "rounds" not in bracket:
            raise ServiceException("Invalid bracket passed in", 400)

        # Get actual bracket from database as a starting point
        original_bracket = self.get_bracket(bracket_id)

        if self.user.get("admin") == 0:
            # If you don't own the bracket, no go
            if original_bracket.get("user_id") != self.user.get("user_id"):
                raise ServiceException("You do not have permission to update this bracket", 403)

            # If the tournament isn't active, no go
            tournament = self.da.get_tournament(original_bracket.get("tournament_id"))
            if not tournament.get("active"):
                raise ServiceException("This tournament is already closed. No more updates are permitted.", 403)

        # Validate that the new bracket's rounds match the size of the original
        original_rounds, rounds = original_bracket.get("rounds"), bracket.get("rounds")
        if len(original_rounds) != len(rounds):
            raise ServiceException("Invalid bracket size passed in. {} != {}".format(len(original_rounds), len(rounds)), 400)

        # Update the name
        original_bracket["name"] = bracket.get("name")

        # Find and create any new players in the bracket
        self.create_new_players(rounds)

        # Update all of the matches
        for original_round, round in zip(original_rounds, rounds):
            if len(original_round) != len(round):
                raise ServiceException("Invalid round size passed in. {} != {}".format(len(original_round), len(round)), 400)

            for original_match, match in zip(original_round, round):
                # Only update the matches that have changed
                if original_match.get("player1_id") != match.get("player1_id") or original_match.get("player2_id") != match.get("player2_id") or \
                        original_match.get("seed1") != match.get("seed1") or original_match.get("seed2") != match.get("seed2") or original_match.get("winner_id") != match.get("winner_id"):
                    original_match["player1_id"] = match.get("player1_id")
                    original_match["player2_id"] = match.get("player2_id")
                    original_match["seed1"] = match.get("seed1")
                    original_match["seed2"] = match.get("seed2")
                    original_match["winner_id"] = match.get("winner_id")
                    self.da.update_match(original_match.get("match_id"), original_match)

        # If this is an update to a master bracket, update the other brackets
        if original_bracket.get("user_id") is None:
            # Make sure all brackets have the correct first round (this happens when someone pulls out or a qualifier gets added right before the tourney)
            for bracket in self.da.get_brackets(original_bracket.get("tournament_id")):
                if bracket.get("bracket_id") == original_bracket.get("bracket_id"):
                    continue

                # Populate all the matches
                bracket = self.fill_bracket(bracket)

                for master_match, match in zip(original_bracket.get("rounds")[0], bracket.get("rounds")[0]):
                    # Only update matches that have changed
                    if master_match.get("player1_id") != match.get("player1_id") or master_match.get("player2_id") != match.get("player2_id") or \
                            master_match.get("seed1") != match.get("seed1") or master_match.get("seed2") != match.get("seed2"):
                        match["player1_id"] = master_match.get("player1_id")
                        match["player2_id"] = master_match.get("player2_id")
                        match["seed1"] = master_match.get("seed1")
                        match["seed2"] = master_match.get("seed2")
                        self.da.update_match(match.get("match_id"), match)

        self.da.update_bracket(bracket_id, original_bracket)
        return self.get_bracket(bracket_id)

    def create_new_players(self, rounds):
        new_players = []
        for round in rounds:
            for match in round:
                if match.get("player1_id") is None and match.get("player1_name") is not None and match.get("player1_name") not in new_players:
                    new_players.append(match.get("player1_name"))
                if match.get("player2_id") is None and match.get("player2_name") is not None and match.get("player2_name") not in new_players:
                    new_players.append(match.get("player2_name"))
        if len(new_players) != 0:
            self.da.create_players([{"name": player} for player in new_players])

        # Looks up and adds player_ids to matches
        all_players = self.da.get_players()
        player_look_up = {}
        for player in all_players:
            player_look_up[player["name"]] = player.get("player_id")
        for round in rounds:
            for match in round:
                if match.get("player1_id") is None and match.get("player1_name") is not None:
                    match["player1_id"] = player_look_up[match.get("player1_name")]
                if match.get("player2_id") is None and match.get("player2_name") is not None:
                    match["player2_id"] = player_look_up[match.get("player2_name")]

    def get_my_bracket(self, tournament_id):
        bracket = self.da.get_bracket(tournament_id = tournament_id, user_id = self.user["user_id"])
        if bracket is None:
            raise ServiceException("No bracket existed for user_id: {} in tournament_id: {}".format(tournament_id, self.user["user_id"]), 404)
        bracket = self.fill_bracket(bracket)
        return bracket

    def get_bracket(self, bracket_id):
        bracket = self.da.get_bracket(bracket_id)
        if bracket is None:
            raise ServiceException("This bracket does not exist", 400)
        bracket = self.fill_bracket(bracket)
        return bracket

    def fill_bracket(self, bracket):
        bracket["rounds"] = self.get_rounds(bracket["bracket_id"])

        # this first part is necessary to not break the code if the master bracket has not been created yet (I think this may only be applicable for
        # tests because people will not be able to get their bracket if the master bracket hasn't been created but we do this in tests)
        tournament = self.da.get_tournament(bracket["tournament_id"])
        if self.da.get_bracket(tournament["master_bracket_id"]) is None:
            bracket["score"] = 0
            return bracket

        bracket["score"] = self.da.get_score(bracket["bracket_id"])
        return bracket

    def get_rounds(self, bracket_id):
        matches = self.da.get_matches(bracket_id)
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

    def create_bracket_and_matches(self, bracket):
        new_bracket_id = self.da.create_bracket(bracket)["bracket_id"]
        self.da.create_matches(new_bracket_id, bracket["rounds"])
        return new_bracket_id
