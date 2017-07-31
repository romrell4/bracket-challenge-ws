import unittest
import json

import handler
import da

from res import properties

EVENT = {
    "headers": {
        "Authorization": properties.test_token
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

class MyTest(unittest.TestCase):
    def test_users(self):
        # Register as a new user
        response = execute("/users", "POST")
        assert_success(response)

        # Login as an existing user
        response = execute("/users", "POST")
        assert_success(response)
        user_id = json.loads(response["body"])["user_id"]

        # Delete user
        da.delete_user(user_id)

        # self.run_all_simple_tests(
        #     "user", "users",
        #     {"username": "test", "name": "test"},
        #     {"username": "test2", "name": "test2"},
        #     lambda lhs, rhs: lhs["username"] == rhs["username"]
        # )

    # @staticmethod
    # def run_all_simple_tests(singular, plural, original_obj, updated_obj, equals_function):
    #     path_param = "{}Id".format(singular)
    #     id_key = "{}_id".format(singular)
    #     endpoint1 = "/{}".format(plural)
    #     endpoint2 = "/{}/{{{}}}".format(plural, path_param)
    #
    #     # Get all
    #     response = execute(endpoint1)
    #     assert_success(response)
    #
    #     # Create
    #     response = execute(endpoint1, "POST", body = json.dumps(original_obj))
    #     assert_success(response)
    #     id = json.loads(response["body"])[id_key]
    #
    #     # Get one
    #     response = execute(endpoint2, path_params = {path_param: id})
    #     assert_success(response)
    #     obj = json.loads(response["body"])
    #     assert equals_function(obj, original_obj)
    #
    #     # Update
    #     response = execute(endpoint2, "PUT", path_params = {path_param: id}, body = json.dumps(updated_obj))
    #     assert_success(response)
    #     obj = json.loads(response["body"])
    #     assert equals_function(obj, updated_obj)
    #
    #     # Delete
    #     response = execute(endpoint2, "DELETE", path_params = {path_param: id})
    #     assert_success(response)
