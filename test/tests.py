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
    "body": ""
}

def execute(resource, method = "GET", path_params = None, body = None):
    EVENT["resource"] = resource
    EVENT["httpMethod"] = method
    if path_params is not None:
        EVENT["pathParameters"] = path_params
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

    def test_get_bracket(self):
        response = execute("/tournaments/{tournamentId}/brackets/{bracketId}", path_params = {"tournamentId": 1, "bracketId": 3})
        assert_success(response)
        body = get_body(response)
        print(json.dumps(body, indent = 4))
        assert "rounds" in body
        assert len(body["rounds"]) > 1
