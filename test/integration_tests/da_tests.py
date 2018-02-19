from unittest2 import TestCase
from datetime import date, datetime, timedelta

from da import Dao

class DaoTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.da = Dao()

    def test_users(self):
        dict1 = {"username": "test", "name": "test"}
        dict2 = {"username": "test", "name": "test2"}
        self.run_simple_tests(self.da.get_users, self.da.create_user, self.da.update_user, self.da.delete_user, "user_id", dict1, dict2)

    def test_players(self):
        dict1 = {"name": "test"}
        dict2 = {"name": "test2"}
        self.run_simple_tests(self.da.get_players, self.da.create_player, self.da.update_player, self.da.delete_player, "player_id", dict1, dict2)

        # test batch insert of players
        self.assertEqual(0, len([player for player in self.da.get_players() if player["name"].startswith("test")]))
        self.da.create_players([dict1, dict2])
        players = self.da.get_players()
        results = [player for player in players if player["name"].startswith("test")]
        self.assertEqual(2, len(results))
        for player in results:
            self.da.delete_player(player["player_id"])

    def test_tournaments(self):
        dict1 = {"name": "test"}
        dict2 = {"name": "test", "master_bracket_id": 0, "draws_url": "test_draws.com", "image_url": "test_image.com", "start_date": date.today(), "end_date": date.today()}
        self.run_simple_tests(self.da.get_tournaments, self.da.create_tournament, self.da.update_tournament, self.da.delete_tournament, "tournament_id", dict1, dict2)

        # Test the dates and temporary active flag
        dict1["start_date"] = date.today() + timedelta(days = 1)
        dict1["end_date"] = date.today() + timedelta(days = 2)
        tournament = self.da.create_tournament(dict1)
        try:
            start_date = datetime.strptime(tournament.get("start_date"), "%Y-%m-%d").date()
            self.assertGreater(start_date, date.today())
            self.assertTrue(tournament.get("active"))
        finally:
            self.da.delete_tournament(tournament.get("tournament_id"))

    def test_brackets(self):
        tournament = self.da.create_tournament({"name": "test"})
        user1 = self.da.create_user({"username": "test", "name": "test"})
        user2 = self.da.create_user({"username": "test2", "name": "test2"})
        try:
            dict1 = {"user_id": user1["user_id"], "tournament_id": tournament["tournament_id"], "name": "test"}
            dict2 = {"user_id": user1["user_id"], "tournament_id": tournament["tournament_id"], "name": "test2"}
            self.run_simple_tests(None, self.da.create_bracket, self.da.update_bracket, self.da.delete_bracket, "bracket_id", dict1, dict2)

            # Testing the get_brackets with id
            self.da.create_bracket({"user_id": user1["user_id"], "tournament_id": tournament["tournament_id"], "name": "test"})
            self.da.create_bracket({"user_id": user2["user_id"], "tournament_id": tournament["tournament_id"], "name": "test"})
            brackets = self.da.get_brackets(tournament["tournament_id"])
            self.assertEqual(2, len(brackets))

            # Testing the get_brackets with tournament and user
            bracket = self.da.get_bracket(tournament_id = tournament["tournament_id"], user_id = user1["user_id"])
            self.assertIsNotNone(bracket)

            bracket = self.da.get_bracket(tournament_id = tournament["tournament_id"], user_id = 0)
            self.assertIsNone(bracket)

        finally:
            self.da.delete_tournament(tournament["tournament_id"])
            self.da.delete_user(user1["user_id"])
            self.da.delete_user(user2["user_id"])

    def test_matches(self):
        user = self.da.create_user({"username": "test", "name": "test"})
        player1 = self.da.create_player({"name": "test player1"})
        player2 = self.da.create_player({"name": "test player2"})
        tournament = self.da.create_tournament({"name": "test"})
        try:
            bracket = self.da.create_bracket({"user_id": user["user_id"], "tournament_id": tournament["tournament_id"],
                                         "name": "test", "score": 20})
            dict1 = {"bracket_id": bracket["bracket_id"], "round": 1, "position": 1, "player1_id": player1["player_id"],
                     "player2_id": player2["player_id"], "seed1": 1, "winner_id": player1["player_id"]}
            dict2 = {"bracket_id": bracket["bracket_id"], "round": 1, "position": 2, "player1_id": player1["player_id"],
                     "player2_id": player2["player_id"], "seed1": 1, "winner_id": player1["player_id"]}
            self.run_simple_tests(None, self.da.create_match, self.da.update_match, self.da.delete_match, "match_id", dict1, dict2)

            # Testing get all matches
            match = self.da.create_match({"bracket_id": bracket["bracket_id"], "round": 1, "position": 1, "player1_id": player1["player_id"],
                             "seed1": 1, "winner_id": player1["player_id"]})
            matches = self.da.get_matches(bracket["bracket_id"])
            self.assertIsNotNone(matches)
            self.assertEqual(1, len(matches))
            self.da.delete_match(match["match_id"])

            # test batch insert matches
            rounds = [
                [
                    {
                        "round": 1,
                        "position": 1,
                        "player1_id": player1["player_id"],
                        "seed1": 1,
                        "winner_id": player1["player_id"]
                    },
                    {
                        "round": 1,
                        "position": 2
                    }
                ],
                [
                    {
                        "round": 2,
                        "position": 1
                    }
                ]
            ]
            self.da.create_matches(bracket["bracket_id"], rounds)
            matches = self.da.get_matches(bracket["bracket_id"])
            self.assertIsNotNone(matches)
            self.assertEqual(3, len(matches))

        finally:
            self.da.delete_tournament(tournament["tournament_id"])
            self.da.delete_player(player1["player_id"])
            self.da.delete_player(player2["player_id"])
            self.da.delete_user(user["user_id"])

    def test_score(self):
        tournament = self.da.create_tournament({"name": "test"})
        tournament_id = tournament["tournament_id"]
        master_bracket = self.da.create_bracket({"tournament_id": tournament_id, "name": "master"})
        tournament["master_bracket_id"] = master_bracket["bracket_id"]
        self.da.update_tournament(tournament_id, tournament)
        test_bracket = self.da.create_bracket({"tournament_id": tournament_id, "name": "test"})
        self.da.create_matches(master_bracket["bracket_id"], [[{"round": 1, "position": 1, "winner_id": 1}, {"round": 1, "position": 2, "winner_id": 2}], [{"round": 2, "position": 1, "winner_id": 1}]])
        self.da.create_matches(test_bracket["bracket_id"], [[{"round": 1, "position": 1, "winner_id": 1}, {"round": 1, "position": 2, "winner_id": 2}], [{"round": 2, "position": 1, "winner_id": 1}]])
        try:
            score = self.da.get_score(test_bracket["bracket_id"])
            self.assertEqual(4, score)
        finally:
            self.da.delete_tournament(tournament_id)

    def run_simple_tests(self, get_all, create, update, delete, id_key, create_dict, update_dict):
        # Test get all
        if get_all is not None:
            objs = get_all()
            self.assertIsNotNone(objs)

        # Test create (which also tests get)
        obj = create(create_dict)
        obj_id = None
        try:
            self.assertIsNotNone(obj)
            obj_id = obj[id_key]

            # Test update
            new_obj = update(obj_id, update_dict)
            self.assertNotEqual(obj, new_obj)
        finally:
            if obj_id is not None:
                # Test delete
                delete(obj_id)

