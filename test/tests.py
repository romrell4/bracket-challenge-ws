import unittest
import json

import handler
import da

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
        EVENT["queryParameters"] = query_params
    if body is not None:
        EVENT["body"] = body
    return handler.lambda_handler(EVENT, None)

def assert_success(response):
    assert response["statusCode"] < 300

def get_body(response):
    return json.loads(response["body"])

class MyTest(unittest.TestCase):
    def test_login(self):
        # Register as a new user
        response = execute("/users", "POST")
        assert_success(response)

        # Login as an existing user
        response = execute("/users", "POST")
        assert_success(response)
        user_id = get_body(response)["user_id"]

        # Delete user
        da.delete_user(user_id)

    def test_get_tournaments(self):
        response = execute("/tournaments")
        assert_success(response)

    def _test_get_bracket(self):
        # TODO: eric is a bad example and should have done test cases for invalid parameters
        # TODO: this test should insert a new tournament to test with and then delete it at the end

        response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": 1, "bracketId": 3})
        assert_success(response)
        body = get_body(response)
        print(json.dumps(body, indent = 4))
        assert "rounds" in body
        assert len(body["rounds"]) > 1

    def test_get_brackets(self):
        # Invalid tournamentId
        response = execute("/tournaments/{tournamentId}/brackets", path_params = {"tournamentId": 0})
        assert_success(response)
        assert len(get_body(response)) == 0
        print(response)

        # empty tournament
        tournament = da.create_tournament({"name": "test", "master_bracket_id": 0})
        response = execute("/tournaments/{tournamentId}/brackets", path_params = {"tournamentId": tournament["tournament_id"]})
        assert_success(response)
        assert len(get_body(response)) == 0
        print(response)

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
            print(response)

            # With valid userId
            response = execute("/tournaments/{tournamentId}/brackets", path_params = {"tournamentId": tournament["tournament_id"]}, query_params = {"mine": "true"})
            assert_success(response)
            assert len(get_body(response)) == 1
            print(response)
        finally:
            da.delete_bracket(bracket1["bracket_id"])
            da.delete_bracket(bracket2["bracket_id"])
            da.delete_user(other_user["user_id"])
            da.delete_user(user_id)
            da.delete_tournament(tournament["tournament_id"])

    def test_create_bracket(self):


