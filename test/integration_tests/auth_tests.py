import auth
import os
from unittest import TestCase

from service_exception import ServiceException

class AuthTest(TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "../../src/firebase_creds.json"

    def test_no_token(self):
        with self.assertRaises(ServiceException) as e:
            auth.validate_user({"headers": {}})
        self.assertEqual(401, e.exception.status_code)
        self.assertEqual("Unable to find token in request", e.exception.error_message)

    #TODO: Test facebook stuff?

    def test_invalid_token(self):
        with self.assertRaises(ServiceException) as e:
            auth.validate_user({"headers": {"x-firebase-token": ""}})
        self.assertEqual(401, e.exception.status_code)
        self.assertEqual("Unable to authenticate with Firebase. Please log out and back in.", e.exception.error_message)

    # def test_valid_token(self):
    #     user = auth.validate_user({"headers": {"x-firebase-token": "TODO: Get a token to test"}})
    #     self.assertIn("email", user)
    #     self.assertIn("name", user)
