from unittest2 import TestCase

from manager import Manager
from res import properties
from service_exception import ServiceException
import da

class ManagerTest(TestCase):
    def setUp(self):
        self.become_tester()

    def become_admin(self):
        self.manager = Manager(properties.admin_username)

    def become_tester(self):
        self.manager = Manager(properties.test_username)

    def test_create_tournament(self):
        # Test with an empty tournament
        e = assert_error(lambda: self.manager.create_tournament(None))
        assert e.status_code == 400

        original_tournament = {"name": "Test"}

        # testing a non-admin user trying to create a tournament
        e = assert_error(lambda: self.manager.create_tournament(original_tournament))
        assert e.status_code == 403

        # testing an admin creating a valid tournament
        self.manager = Manager(properties.admin_username)
        new_tournament = self.manager.create_tournament(original_tournament)
        try:
            assert new_tournament.get("tournament_id") is not None
        finally:
            da.delete_tournament(new_tournament["tournament_id"])

    def test_update_bracket(self):
        tournament_id = da.create_tournament({"name": "Test"})["tournament_id"]
        new_player_id = None
        try:
            # Test null bracket
            e = assert_error(lambda: self.manager.update_bracket(None, None))
            self.assertEqual(400, e.status_code)

            # Test bracket with no name
            e = assert_error(lambda: self.manager.update_bracket(1, {}))
            self.assertEqual(400, e.status_code)

            # Test bracket with no rounds
            e = assert_error(lambda: self.manager.update_bracket(1, {"name": "Test"}))
            self.assertEqual(400, e.status_code)

            # Test non-existent bracket id
            e = assert_error(lambda: self.manager.update_bracket(-1, {"name": "Test", "rounds": []}))
            self.assertEqual(400, e.status_code)

            # Create master/user bracket
            master_bracket = da.create_bracket({"tournament_id": tournament_id, "name": "Test - Results"})
            master_bracket["rounds"] = []
            test_bracket = da.create_bracket({"user_id": self.manager.user["user_id"], "tournament_id": tournament_id, "name": "Test"})
            da.create_match({"bracket_id": test_bracket["bracket_id"], "round": 1, "position": 1})
            test_bracket = self.manager.get_bracket(test_bracket["bracket_id"])

            # Test updating master as non-admin
            e = assert_error(lambda: self.manager.update_bracket(master_bracket["bracket_id"], master_bracket))
            self.assertEqual(403, e.status_code)

            # Test updating your bracket as non-admin
            test_bracket["name"] = "New Name"
            new_bracket = self.manager.update_bracket(test_bracket["bracket_id"], test_bracket)
            self.assertEqual("New Name", new_bracket["name"])

            # Test updating someone else's bracket as admin
            test_bracket["name"] = "Another New Name"
            self.become_admin()
            new_bracket = self.manager.update_bracket(test_bracket["bracket_id"], test_bracket)
            self.assertEqual("Another New Name", new_bracket["name"])

            # Test updating master bracket as admin
            master_bracket["name"] = "New Name"
            new_bracket = self.manager.update_bracket(master_bracket["bracket_id"], master_bracket)
            self.assertEqual("New Name", new_bracket["name"])

            # Test updating bracket's rounds
            self.become_tester()
            test_bracket["rounds"][0][0]["player1_id"] = 1
            new_bracket = self.manager.update_bracket(test_bracket["bracket_id"], test_bracket)
            self.assertEqual(1, new_bracket["rounds"][0][0]["player1_id"])

            # Test updating bracket's rounds with unknown player
            test_bracket["rounds"][0][0]["player2_name"] = "Tester"
            new_bracket = self.manager.update_bracket(test_bracket["bracket_id"], test_bracket)
            new_player_id = new_bracket["rounds"][0][0]["player2_id"]
            self.assertIsNotNone(new_player_id)

        finally:
            da.delete_tournament(tournament_id)
            if new_player_id is not None:
                da.delete_player(new_player_id)

def assert_error(statement):
    try:
        statement()
        assert False
    except ServiceException as e:
        return e
