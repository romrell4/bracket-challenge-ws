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

class UsersTest(unittest.TestCase):
    def test1(self):
        response = handler.lambda_handler(EVENT, None)
        print(response)
        assert response["statusCode"] < 300
