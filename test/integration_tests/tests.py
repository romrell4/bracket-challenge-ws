import unittest
import json
import math

import handler
import da

from service_exception import ServiceException
from res import properties

EVENT = {
    "headers": {
        "Token": properties.test_token
    },
    "httpMethod": "GET",
    "resource": "/brackets",
    "pathParameters": {

    },
    "queryParameters": {

    },
    "body": ""
}

def execute(resource, method = "GET", path_params = {}, query_params = {}, body = ""):
    EVENT["resource"] = resource
    EVENT["httpMethod"] = method
    EVENT["pathParameters"] = path_params
    EVENT["queryStringParameters"] = query_params
    EVENT["body"] = body
    return handler.lambda_handler(EVENT, None)

def assert_success(response):
    assert response["statusCode"] < 300

def get_body(response):
    return json.loads(response["body"])

def create_bracket(rounds, only_first_round, commit_to_database = True, player_ids = None, tournament = None):
    if player_ids is None:
        # creates new players
        players = []
        for i in range(int(math.pow(2, rounds))):
            player = {"name": "_player" + str(i + 1)}
            if not commit_to_database:
                player["player_id"] = i + 1
            players.append(player)

        if commit_to_database:
            # this creates players and appends all their ids to player_ids
            da.create_players(players)
            player_ids = [player["player_id"] for player in da.get_players() if player["name"].startswith("_player")]
        else:
            # This puts only the players' ids into player_ids
            player_ids = [player["player_id"] for player in players]
    else:
        # makes sure that they passed in enough players to create the tournament
        assert len(player_ids) == int(math.pow(2, rounds))

    if tournament is None:
        tournament = {"name": "test"}
        if commit_to_database:
            tournament = da.create_tournament(tournament)

    bracket = {"name": "test"}
    if commit_to_database:
        bracket["tournament_id"] = tournament["tournament_id"]
        bracket = da.create_bracket(bracket)

    bracket["rounds"] = []
    for round in range(rounds):
        round_array = []
        positions = int(len(player_ids) / math.pow(2, round + 1))
        for position in range(positions):
            match = {
                "round": round + 1,
                "position": position + 1
            }

            player1_index = int(position * math.pow(2, round + 1))

            if round == 0 or not only_first_round:
                match["player1_id"] = player_ids[player1_index]
                match["player2_id"] = player_ids[int(player1_index + math.pow(2, round))]

            if not only_first_round:
                match["winner_id"] = player_ids[player1_index]

            round_array.append(match)
        bracket["rounds"].append(round_array)
    if commit_to_database:
        da.create_matches(bracket["bracket_id"], bracket["rounds"])
    return bracket, player_ids

class MyTest(unittest.TestCase):
    def setUp(self):
        try:
            self.user = da.create_user({"username": properties.test_username, "name": "Test User"})
        except ServiceException:
            self.user = da.get_user_by_username(properties.test_username)

    def test_login(self):
        da.delete_user(self.user["user_id"])

        # Register as a new user
        response = execute("/users", "POST")
        assert_success(response)

        # Login as an existing user
        response = execute("/users", "POST")
        assert_success(response)

    def test_get_players(self):
        response = execute("/players")
        assert_success(response)

    def test_get_tournaments(self):
        response = execute("/tournaments")
        assert_success(response)

    def test_create_tournament(self):
        tournament = {"name": "Test"}
        # testing a nonadmin user trying to create a tournament
        response = execute("/tournaments", "POST", body = json.dumps(tournament))
        assert response["statusCode"] == 403

        # testing an admin trying to create a tournament without a body
        EVENT["headers"]["Token"] = properties.admin_token
        response = execute("/tournaments", "POST")
        assert response["statusCode"] == 400

        # testing an admin creating a valid tournament
        response = execute("/tournaments", "POST", body = json.dumps(tournament))
        body = get_body(response)
        try:
            assert_success(response)
            assert len(body) > 0

        finally:
            EVENT["headers"]["Token"] = properties.test_token
            da.delete_tournament(body["tournament_id"])

    def test_update_tournament(self):
        # Create a test tournament and update something in it
        tournament = da.create_tournament({"name": "Test"})
        tournament["active"] = True

        # Test a non-admin
        response = execute("/tournaments/{tournamentId}", "PUT", path_params = {"tournamentId": tournament["tournament_id"]}, body = json.dumps(tournament))
        assert response["statusCode"] == 403

        EVENT["headers"]["Token"] = properties.admin_token

        # Test without a valid tournament body
        response = execute("/tournaments/{tournamentId}", "PUT", path_params = {"tournamentId": tournament["tournament_id"]})
        assert response["statusCode"] == 400

        # Test without a valid tournament id
        response = execute("/tournaments/{tournamentId}", "PUT", body = json.dumps(tournament))
        assert response["statusCode"] == 400

        # Test a valid tournament update and make sure it updated
        response = execute("/tournaments/{tournamentId}", "PUT", path_params = {"tournamentId": tournament["tournament_id"]}, body = json.dumps(tournament))
        assert_success(response)
        assert get_body(response)["active"] == 1

    def test_get_my_bracket(self):
        tournament_id = da.create_tournament({"name": "test"})["tournament_id"]
        try:
            # Invalid tournamentId
            response = execute("/tournaments/{tournamentId}/brackets/mine", path_params = {"tournamentId": 0})
            assert response["statusCode"] == 404

            # User doesn't have a bracket
            response = execute("/tournaments/{tournamentId}/brackets/mine", path_params = {"tournamentId": tournament_id})
            assert response["statusCode"] == 404

            # Valid bracket
            da.create_bracket({"user_id": self.user["user_id"], "tournament_id": tournament_id, "name": "test"})
            response = execute("/tournaments/{tournamentId}/brackets/mine", path_params = {"tournamentId": tournament_id})
            assert_success(response)
        finally:
            da.delete_tournament(tournament_id)

    def test_get_bracket(self):

        # change this number to change the size of a new tournament
        rounds = 2
        bracket1, player_ids = create_bracket(rounds, True)
        tournament1_id = bracket1["tournament_id"]
        bracket1_id = bracket1["bracket_id"]

        bracket2, player_ids = create_bracket(rounds, False, True, player_ids)
        tournament2_id = bracket2["tournament_id"]
        bracket2_id = bracket2["bracket_id"]

        try:
            # Invalid bracketId
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": tournament1_id, "bracketId": 0})
            assert response["statusCode"] == 400

            # Valid bracketId on a new "master" bracket
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": tournament1_id, "bracketId": bracket1_id})
            assert_success(response)
            body = get_body(response)
            assert "rounds" in body
            assert len(body["rounds"]) == rounds
            for round in range(rounds):
                assert len(body["rounds"][round]) == int(len(player_ids) / math.pow(2, round + 1))

            # Valid bracketId on a full bracket
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": tournament2_id, "bracketId": bracket2_id})
            assert_success(response)
            body = get_body(response)
            assert "rounds" in body
            assert len(body["rounds"]) == rounds
            for round in range(rounds):
                assert len(body["rounds"][round]) == int(len(player_ids) / math.pow(2, round + 1))

        finally:
            da.delete_tournament(tournament1_id)
            da.delete_tournament(tournament2_id)
            for player_id in player_ids:
                da.delete_player(player_id)

    def test_get_brackets(self):
        # Invalid tournamentId
        response = execute("/tournaments/{tournamentId}/brackets", path_params = {"tournamentId": 0})
        assert_success(response)
        assert len(get_body(response)) == 0

        # empty tournament
        tournament = da.create_tournament({"name": "test", "master_bracket_id": 0})
        response = execute("/tournaments/{tournamentId}/brackets", path_params = {"tournamentId": tournament["tournament_id"]})
        assert_success(response)
        assert len(get_body(response)) == 0

        # non empty tournament
        other_user = da.create_user({"username": "test_user", "name": "test"})
        bracket1 = da.create_bracket({"user_id": self.user["user_id"], "tournament_id": tournament["tournament_id"], "name": "test"})
        bracket2 = da.create_bracket({"user_id": other_user["user_id"], "tournament_id": tournament["tournament_id"], "name": "test"})

        try:
            response = execute("/tournaments/{tournamentId}/brackets", path_params = {"tournamentId": tournament["tournament_id"]})
            assert_success(response)
            body = get_body(response)
            assert len(body) == 2
            for bracket in body:
                assert "rounds" in bracket
                assert "score" in bracket

        finally:
            da.delete_bracket(bracket1["bracket_id"])
            da.delete_bracket(bracket2["bracket_id"])
            da.delete_user(other_user["user_id"])
            da.delete_tournament(tournament["tournament_id"])

    def test_create_bracket(self):
        bracket = {"name": "Master", "rounds": [
            [
                {
                    "round": 1,
                    "position": 1,
                    "player1_id": 1,
                    "player2_id": 2
                },
                {
                    "round": 1,
                    "position": 2,
                    "player1_id": 3,
                    "player2_id": 4
                }
            ],
            [
                {
                    "round": 2,
                    "position": 1
                },
            ]
        ]}
        bracket_with_names = {"name": "Master", "rounds": [
            [
                {
                    "round": 1,
                    "position": 1,
                    "player1_name": "_player1",
                    "player2_name": "_player2"
                },
                {
                    "round": 1,
                    "position": 2,
                    "player1_name": "_player3",
                    "player2_name": "_player4"
                }
            ],
            [
                {
                    "round": 2,
                    "position": 1
                },
            ]
        ]}
        tournament = da.create_tournament({"name": "Test"})
        tournament_id = tournament["tournament_id"]

        try:
            # Invalid  bracket
            response = execute("/tournaments/{tournamentId}/brackets", "POST", path_params = {"tournamentId": tournament_id})
            assert response["statusCode"] == 400

            # Invalid tournamentId
            response = execute("/tournaments/{tournamentId}/brackets", "POST", path_params = {"tournamentId": 0}, body = json.dumps(bracket))
            assert response["statusCode"] == 400

            # Test without Admin privileges (creating a master bracket)
            response = execute("/tournaments/{tournamentId}/brackets", "POST", path_params = {"tournamentId": tournament_id}, body = json.dumps(bracket))
            assert response["statusCode"] == 403

            # test with admin privileges trying to create a blank master bracket
            EVENT["headers"]["Token"] = properties.admin_token
            response = execute("/tournaments/{tournamentId}/brackets", "POST", path_params = {"tournamentId": tournament_id}, body = json.dumps({"name": "test"}))
            assert response["statusCode"] == 400

            # test with Admin privileges with all new players
            response = execute("/tournaments/{tournamentId}/brackets", "POST", path_params = {"tournamentId": tournament_id}, body = json.dumps(bracket_with_names))
            assert_success(response)
            tournament = da.get_tournament(tournament_id)
            master_id = tournament["master_bracket_id"]
            assert master_id is not None
            master_bracket = da.get_bracket(master_id)
            assert master_bracket is not None
            assert master_bracket["name"] != bracket["name"]
            player_ids = [player["player_id"] for player in da.get_players() if player["name"].startswith("_player")]
            assert len(player_ids) == 4
            body = get_body(response)
            for i in range(len(body["rounds"])):
                for match in body["rounds"][i]:
                    if i == 0:
                        assert match["player1_id"] in player_ids
                        assert match["player2_id"] in player_ids

            tournament["master_bracket_id"] = None
            da.update_tournament(tournament_id, tournament)

            # test with Admin privileges with all existing players
            response = execute("/tournaments/{tournamentId}/brackets", "POST", path_params = {"tournamentId": tournament_id}, body = json.dumps(bracket))
            assert_success(response)
            tournament = da.get_tournament(tournament_id)
            master_id = tournament["master_bracket_id"]
            assert master_id is not None
            master_bracket = da.get_bracket(master_id)
            assert master_bracket is not None
            assert master_bracket["name"] != bracket["name"]

            EVENT["headers"]["Token"] = properties.test_token

            # test with master
            bracket = {"name": "test"}

            response = execute("/tournaments/{tournamentId}/brackets", "POST", path_params = {"tournamentId": tournament_id}, body = json.dumps(bracket))
            assert_success(response)
            user_bracket = da.get_bracket(tournament_id = tournament_id, user_id = self.user["user_id"])
            user_matches = da.get_matches(user_bracket["bracket_id"])
            master_id = da.get_tournament(tournament_id)["master_bracket_id"]
            master_matches = da.get_matches(master_id)
            assert len(user_matches) == len(master_matches)
            for (user_match, master_match) in zip(user_matches, master_matches):
                assert user_match["player1_id"] == master_match["player1_id"] and user_match["player2_id"] == master_match["player2_id"] \
                       and user_match["round"] == master_match["round"] and user_match["position"] == master_match["position"]

            # test with preexisting bracket
            response = execute("/tournaments/{tournamentId}/brackets", "POST", path_params = {"tournamentId": tournament_id}, body = json.dumps(bracket))
            assert response["statusCode"] == 412

        finally:
            EVENT["headers"]["Token"] = properties.test_token
            da.delete_tournament(tournament_id)
            for player_id in player_ids:
                da.delete_player(player_id)

    def test_scores(self):
        # change this number to change the rounds
        rounds = 3
        master_bracket, player_ids = create_bracket(rounds, True, True)

        # This updates the tournament so that it has a master bracket
        tournament = da.get_tournament(master_bracket["tournament_id"])
        tournament["master_bracket_id"] = master_bracket["bracket_id"]
        da.update_tournament(tournament["tournament_id"], tournament)

        test_bracket, player_ids = create_bracket(rounds, True, True, player_ids, tournament)
        full_master_bracket, player_ids = create_bracket(rounds, False, True, player_ids, tournament)
        full_test_bracket, player_ids = create_bracket(rounds, False, True, player_ids, tournament)

        # Getting the test_bracket back through the handler because then the "rounds" will include the match_ids which is necessary for one of the tests
        test_bracket = get_body(execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": tournament["tournament_id"], "bracketId": test_bracket["bracket_id"]}))

        try:
            # test a tournament with no winners yet
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": tournament["tournament_id"], "bracketId": test_bracket["bracket_id"]})
            assert_success(response)
            body = get_body(response)
            assert "score" in body
            assert body["score"] == 0

            # test one winner in each round
            tournament["master_bracket_id"] = full_master_bracket["bracket_id"]
            da.update_tournament(tournament["tournament_id"], tournament)
            for test_round, master_round in zip(test_bracket["rounds"], full_master_bracket["rounds"]):
                test_round[0]["winner_id"] = master_round[0]["winner_id"]
                da.update_match(test_round[0]["match_id"], test_round[0])
                response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": tournament["tournament_id"], "bracketId": test_bracket["bracket_id"]})
                assert_success(response)
                body = get_body(response)
                assert "score" in body
                assert body["score"] == master_round[0]["round"]
                test_round[0]["winner_id"] = None
                da.update_match(test_round[0]["match_id"], test_round[0])

            # test a bracket with all winners
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": tournament["tournament_id"], "bracketId": full_test_bracket["bracket_id"]})
            assert_success(response)
            body = get_body(response)
            assert "score" in body

            # This get's total score for all correct
            score = 0
            for round in range(len(body["rounds"])):
                score += (round + 1) * len(body["rounds"][round])
            assert body["score"] == score

        finally:
            da.delete_tournament(tournament["tournament_id"])
            for player_id in player_ids:
                da.delete_player(player_id)

    def tearDown(self):
        da.delete_user(self.user["user_id"])
