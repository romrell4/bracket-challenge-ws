import unittest
import handler
from res import properties

EVENT = {
    "headers": {
        "Authorization": properties.get_auth()
    },
    "httpMethod": "GET",
    "resource": "/brackets",
    "pathParameters": {

    },
    "body": {

    }
}

def setup_event(resource, method = "GET", path_params = None, body = None):
    EVENT["resource"] = resource
    EVENT["httpMethod"] = method
    if path_params is not None:
        EVENT["pathParameters"] = path_params
    if body is not None:
        EVENT["body"] = body

def execute():
    return handler.lambda_handler(EVENT, None)

def assert_success(response):
    assert response["statusCode"] < 300

class UsersTest(unittest.TestCase):
    def test_get_users(self):
        setup_event("/users")
        response = execute()
        assert_success(response)

    def test_get_user(self):
        setup_event("/user/1")
        response = execute()
        assert_success(response)
