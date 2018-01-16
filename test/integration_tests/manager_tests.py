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

def assert_error(statement):
    try:
        statement()
        assert False
    except ServiceException as e:
        return e
