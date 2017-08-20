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

def create_bracket(rounds, only_first_round, commit_to_database = True):
    player_ids = []
    for i in range(int(math.pow(2, rounds))):
        player = {"name": "player" + str(i + 1)}
        if commit_to_database:
            player = da.create_player(player)
        player_ids.append(player["player_id"])

    tournament_id = da.create_tournament({"name": "test"})["tournament_id"]
    bracket = {"tournament_id": tournament_id, "name": "test"}
    if commit_to_database:
        bracket = da.create_bracket(bracket)
    bracket_id = bracket["bracket_id"]

    bracket["rounds"] = []
    for round in range(rounds):
        round_array = []
        positions = int(len(player_ids) / math.pow(2, round + 1))
        for position in range(positions):
            match = {
                "bracket_id": bracket_id,
                "round": round + 1,
                "position": position + 1
            }

            player1_index = int(position * math.pow(2, round + 1))

            if round == 0 or not only_first_round:
                match["player1_id"] = player_ids[player1_index]
                match["player2_id"] = player_ids[int(player1_index + math.pow(2, round))]

            if not only_first_round:
                match["winner_id"] = player_ids[player1_index]

            if commit_to_database:
                match = da.create_match(match)
            round_array.append(match)
        bracket["rounds"].append(round_array)
    return bracket, player_ids

class MyTest(unittest.TestCase):
    def setUp(self):
        try:
            self.user = da.create_user({"username": "test_fqxpeow_user@tfbnw.net", "name": "Test User"})
        except ServiceException:
            self.user = da.get_user_by_username("test_fqxpeow_user@tfbnw.net")

    def _test_login(self):
        da.delete_user(self.user["user_id"])

        # Register as a new user
        response = execute("/users", "POST")
        assert_success(response)

        # Login as an existing user
        response = execute("/users", "POST")
        assert_success(response)

    def _test_get_tournaments(self):
        response = execute("/tournaments")
        assert_success(response)

    def _test_create_tournament(self):
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

    def _test_get_my_bracket(self):
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

    def _test_get_bracket(self):
        tournament1_id = da.create_tournament({"name": "test"})["tournament_id"]
        bracket1_id = da.create_bracket({"tournament_id": tournament1_id, "name": "test"})["bracket_id"]
        da.create_match({"bracket_id": bracket1_id, "round": 1, "position": 1, "player1_id": 1, "player2_id": 2})
        da.create_match({"bracket_id": bracket1_id, "round": 1, "position": 2, "player1_id": 3, "player2_id": 4})
        da.create_match({"bracket_id": bracket1_id, "round": 2, "position": 1})

        tournament2_id = da.create_tournament({"name": "test_full"})["tournament_id"]
        bracket2_id = da.create_bracket({"name": "test2", "tournament_id": tournament2_id})["bracket_id"]

        # change this number to change the size of a new tournament
        rounds = 3
        player_ids = []
        for i in range(int(math.pow(2, rounds))):
            player = da.create_player({"name": "player" + str(i + 1)})
            player_ids.append(player["player_id"])

        # The nested for loop is used to actually create a bracket that is full of matches
        for round in range(rounds):
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
            assert len(body["rounds"]) == rounds
            for round in range(rounds):
                assert len(body["rounds"][round]) == int(len(player_ids) / math.pow(2, round + 1))

        finally:
            da.delete_tournament(tournament1_id)
            da.delete_tournament(tournament2_id)
            for player_id in player_ids:
                da.delete_player(player_id)

    def _test_get_brackets(self):
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
        other_user = da.create_user({"username": "test", "name": "test"})
        bracket1 = da.create_bracket({"user_id": self.user["user_id"], "tournament_id": tournament["tournament_id"], "name": "test", "score": 20})
        bracket2 = da.create_bracket({"user_id": other_user["user_id"], "tournament_id": tournament["tournament_id"], "name": "test", "score": 20})

        try:
            response = execute("/tournaments/{tournamentId}/brackets", path_params = {"tournamentId": tournament["tournament_id"]})
            assert_success(response)
            assert len(get_body(response)) == 2
        finally:
            da.delete_bracket(bracket1["bracket_id"])
            da.delete_bracket(bracket2["bracket_id"])
            da.delete_user(other_user["user_id"])
            da.delete_tournament(tournament["tournament_id"])

    def _test_create_bracket(self):
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
            da.delete_tournament(tournament_id)

    def test_update_bracket(self):
        rounds = 3
        bracket, player_ids = create_bracket(rounds, True)
        tournament_id = bracket["tournament_id"]
        bracket_id = bracket["bracket_id"]
        full_bracket, player_ids_full_bracket = create_bracket(rounds, False)
        try:
            bracket = get_body(execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournament_id": tournament_id, "bracketId": bracket_id}))

            # Test invalid body
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", "PUT", {"tournament_id": tournament_id, "bracketId": bracket_id})
            assert response["statusCode"] == 400

            # Test null name
            bracket["name"] = None
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", "PUT", {"tournament_id": tournament_id, "bracketId": bracket_id}, body = json.dumps(bracket))
            assert response["statusCode"] == 400
            bracket["name"] = "test"

            # test null matches
            rounds = bracket["rounds"]
            bracket["rounds"] = None
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", "PUT", {"tournament_id": tournament_id, "bracketId": bracket_id}, body = json.dumps(bracket))
            assert response["statusCode"] == 400
            bracket["rounds"] = rounds

            # Test invalid bracketId
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", "PUT", {"tournament_id": tournament_id, "bracketId": 0}, body = json.dumps(bracket))
            assert response["statusCode"] == 404

            # test difference in number of rounds
            del bracket["rounds"][0]
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", "PUT", {"tournament_id": tournament_id, "bracketId": bracket_id}, body = json.dumps(bracket))
            assert response["statusCode"] == 400
            bracket["rounds"] = rounds

            # Valid test with no difference
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", "PUT", {"tournament_id": tournament_id, "bracketId": bracket_id}, body = json.dumps(bracket))
            assert_success(response)
            assert get_body(response) == bracket

            # Valid test with one
            bracket_one_change = bracket
            bracket_one_change["rounds"][0][0]["winner_id"] = player_ids[1]
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", "PUT", {"tournament_id": tournament_id, "bracketId": bracket_id}, body = json.dumps(bracket_one_change))
            assert_success(response)
            body = get_body(response)
            assert body != bracket
            assert body == bracket_one_change

            # Valid changing the entire bracket
            bracket_many_changes = bracket
            bracket_many_changes["rounds"] = full_bracket["rounds"]
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", "PUT", {"tournament_id": tournament_id, "bracketId": bracket_id}, body = json.dumps(bracket_many_changes))
            assert_success(response)
            body = get_body(response)
            assert body != bracket
            assert body == bracket_many_changes

        finally:
            da.delete_tournament(full_bracket["tournament_id"])
            da.delete_tournament(tournament_id)
            for player_id in player_ids:
                da.delete_player(player_id)
            for player_id in player_ids_full_bracket:
                da.delete_player(player_id)

    def _test_create_bracket_method(self):
        # Change this number to change the number of rounds in the tournament
        rounds = 3
        bracket, player_ids = create_bracket(rounds, True)
        try:
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": bracket["tournament_id"], "bracketId": bracket["bracket_id"]})
            assert_success(response)
            body = get_body(response)
            assert body is not None
            # print(json.dumps(body, indent = 4))
            assert "rounds" in body
            assert len(body["rounds"]) == rounds
            for round in range(rounds):
                assert len(body["rounds"][round]) == int(len(player_ids) / math.pow(2, round + 1))
                for match in range(len(body["rounds"][round])):
                    assert body["rounds"][round][match]["winner_id"] is None
                    if round == 0:
                        assert body["rounds"][round][match]["player1_id"] is not None
                        assert body["rounds"][round][match]["player2_id"] is not None
                    else:
                        assert body["rounds"][round][match]["player1_id"] is None
                        assert body["rounds"][round][match]["player2_id"] is None


        finally:
            da.delete_tournament(bracket["tournament_id"])
            for player_id in player_ids:
                da.delete_player(player_id)

        # Change this number to change the number of rounds in the tournament
        rounds = 3
        bracket, player_ids = create_bracket(rounds, False)
        try:
            response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": bracket["tournament_id"], "bracketId": bracket["bracket_id"]})
            assert_success(response)
            body = get_body(response)
            assert body is not None
            assert "rounds" in body
            assert len(body["rounds"]) == rounds
            for round in range(rounds):
                assert len(body["rounds"][round]) == int(len(player_ids) / math.pow(2, round + 1))
                for match in range(len(body["rounds"][round])):
                    assert body["rounds"][round][match]["winner_id"] is not None
                    assert body["rounds"][round][match]["player1_id"] is not None
                    assert body["rounds"][round][match]["player2_id"] is not None

        finally:
            da.delete_tournament(bracket["tournament_id"])
            for player_id in player_ids:
                da.delete_player(player_id)

    def tearDown(self):
        da.delete_user(self.user["user_id"])
