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

def execute(resource, method = "GET", path_params = None, query_params = None, body = None):
    EVENT["resource"] = resource
    EVENT["httpMethod"] = method
    if path_params is not None:
        EVENT["pathParameters"] = path_params
    if query_params is not None:
        EVENT["queryStringParameters"] = query_params
    if body is not None:
        EVENT["body"] = body
    return handler.lambda_handler(EVENT, None)

def assert_success(response):
    assert response["statusCode"] < 300

def get_body(response):
    return json.loads(response["body"])

class MyTest(unittest.TestCase):
    def setUp(self):
        try:
            da.create_user({"username": "test_fqxpeow_user@tfbnw.net", "name": "Test User"})
        except ServiceException:
            pass

    def test_login(self):
        user = da.get_user_by_username("test_fqxpeow_user@tfbnw.net")
        da.delete_user(user["user_id"])

        # Register as a new user
        response = execute("/users", "POST")
        assert_success(response)

        # Login as an existing user
        response = execute("/users", "POST")
        assert_success(response)

    def test_get_tournaments(self):
        response = execute("/tournaments")
        assert_success(response)

    def test_get_bracket(self):
        tournament1_id = da.create_tournament({"name": "test"})["tournament_id"]
        bracket1_id = da.create_bracket({"tournament_id": tournament1_id, "name": "test"})["bracket_id"]
        da.create_match({"bracket_id": bracket1_id, "round": 1, "position": 1, "player1_id": 1, "player2_id": 2})
        da.create_match({"bracket_id": bracket1_id, "round": 1, "position": 2, "player1_id": 3, "player2_id": 4})
        da.create_match({"bracket_id": bracket1_id, "round": 2, "position": 1})

        tournament2 = da.create_tournament({"name": "test_full"})
        tournament2_id = tournament2["tournament_id"]
        bracket2 = da.create_bracket({"name": "test2", "tournament_id": tournament2_id})
        bracket2_id = bracket2["bracket_id"]

        # change this number to change the size of a new tournament
        rounds = 3
        player_ids = []
        for i in range(int(math.pow(2, rounds))):
            player = da.create_player({"name": "player" + str(i + 1)})
            player_ids.append(player["player_id"])

        # The nested for loop is used to actually create a bracket that is full of matches
        total_rounds = int(math.log(len(player_ids), 2))
        for round in range(total_rounds):
            positions = int(len(player_ids) / math.pow(2, round + 1))
            for position in range(positions):
                player1_index = int(position * math.pow(2, round + 1))
                da.create_match({
                        "bracket_id": bracket2_id,
                        "round": round + 1,
                        "position": position + 1,
                        "player1_id": player_ids[player1_index],
                        "player2_id": player_ids[int(player1_index + math.pow(2, round))],
                        "winner_id": player_ids[player1_index]
                })

        try:
            # Invalid bracketId
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": tournament1_id, "bracketId": 0})
            assert response["statusCode"] == 400

            # Valid bracketId on a new "master" bracket
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": tournament1_id, "bracketId": bracket1_id})
            assert_success(response)
            body = get_body(response)
            assert "rounds" in body
            assert len(body["rounds"]) == 2
            assert len(body["rounds"][0]) == 2
            assert len(body["rounds"][1]) == 1

            # Valid bracketId on a full bracket
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": tournament2_id, "bracketId": bracket2_id})
            assert_success(response)
            body = get_body(response)
            assert "rounds" in body
            assert len(body["rounds"]) == total_rounds
            for round in range(total_rounds):
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
        response = execute("/users", "POST")
        user_id = get_body(response)["user_id"]
        other_user = da.create_user({"username": "test", "name": "test"})
        bracket1 = da.create_bracket({"user_id": user_id, "tournament_id": tournament["tournament_id"], "name": "test", "score": 20})
        bracket2 = da.create_bracket({"user_id": other_user["user_id"], "tournament_id": tournament["tournament_id"], "name": "test", "score": 20})

        try:
            response = execute("/tournaments/{tournamentId}/brackets", path_params = {"tournamentId": tournament["tournament_id"]})
            assert_success(response)
            assert len(get_body(response)) == 2

            # With valid userId
            response = execute("/tournaments/{tournamentId}/brackets", path_params = {"tournamentId": tournament["tournament_id"]}, query_params = {"mine": "true"})
            assert_success(response)
            assert len(get_body(response)) == 1

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
        tournament = da.create_tournament({"name": "Test"})
        tournament_id = tournament["tournament_id"]

        try:
            # Invalid tournamentId
            response = execute("/tournaments/{tournamentId}/brackets", "POST", path_params = {"tournamentId": 0}, body = json.dumps(bracket))
            assert response["statusCode"] == 400

            # Test without Admin privileges (creating a master bracket)
            response = execute("/tournaments/{tournamentId}/brackets", "POST", path_params = {"tournamentId": tournament_id}, body = json.dumps(bracket))
            assert response["statusCode"] == 403

            # test with Admin privileges
            EVENT["headers"]["Token"] = properties.admin_token
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
            user = da.get_user_by_username("test_fqxpeow_user@tfbnw.net")
            user_brackets = da.get_brackets(tournament_id, user["user_id"])
            assert len(user_brackets) == 1
            bracket = user_brackets[0]
            user_matches = da.get_matches(bracket["bracket_id"])
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
            da.delete_tournament(tournament_id)

    def tearDown(self):
        user = da.get_user_by_username("test_fqxpeow_user@tfbnw.net")
        da.delete_user(user["user_id"])
