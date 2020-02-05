import unittest

from manager import Manager
from model import User

class ManagerUnitTest(unittest.TestCase):

    def test_login(self):
        # TODO: Replace with patch library?
        class MockDao:
            def get_user_by_username(self, username):
                return None
            def create_user(self, new_user):
                return User([None, new_user["username"], new_user["name"], None])

        manager = Manager(MockDao(), None)

        user = manager.login({"email": "test.com"})
        self.assertEqual(user.username, "test.com")
        self.assertEqual(user.name, "Anonymous User")