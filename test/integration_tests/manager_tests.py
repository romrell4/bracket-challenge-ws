import unittest

from manager import Manager
from res import properties
from service_exception import ServiceException
import da

class ManagerTest(unittest.TestCase):
    def setUp(self):
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

    def test_update_tournament(self):
        # Create a test tournament and update something in it
        tournament = da.create_tournament({"name": "Test"})
        tournament["active"] = True

        try:
            # Test a non-admin
            e = assert_error(lambda: self.manager.update_tournament(tournament["tournament_id"], tournament))
            assert e.status_code == 403

            self.manager = Manager(properties.admin_username)

            # Test without a valid tournament body
            e = assert_error(lambda: self.manager.update_tournament(tournament["tournament_id"], None))
            assert e.status_code == 400

            # Test without a valid tournament id
            e = assert_error(lambda: self.manager.update_tournament(None, tournament))
            assert e.status_code == 400

            # Test a valid tournament update and make sure it updated
            new_tournament = self.manager.update_tournament(tournament["tournament_id"], tournament)
            assert new_tournament["active"] == 1
        finally:
            da.delete_tournament(tournament["tournament_id"])

    def test_get_my_bracket(self):
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

def assert_error(statement):
    try:
        statement()
        assert False
    except ServiceException as e:
        return e
