from unittest2 import TestCase
from datetime import datetime, timedelta

from manager import Manager
from res import properties
from service_exception import ServiceException
from da import Dao

class ManagerTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.da = Dao()

    def setUp(self):
        # Make sure the test user is in the database
        if self.da.get_user_by_username(properties.test_username) is None:
            self.da.create_user({"username": properties.test_username, "name": "Test User"})
        self.become_tester()

    def become_admin(self):
        self.manager = Manager(self.da, properties.admin_username)

    def become_tester(self):
        self.manager = Manager(self.da, properties.test_username)

    def test_create_tournament(self):
        # Test with an empty tournament
        e = assert_error(lambda: self.manager.create_tournament(None))
        self.assertEqual(400, e.status_code)

        original_tournament = {"name": "Test"}

        # Test a non-admin user trying to create a tournament
        e = assert_error(lambda: self.manager.create_tournament(original_tournament))
        self.assertEqual(403, e.status_code)

        # Test an admin creating a valid tournament
        self.become_admin()
        new_tournament = self.manager.create_tournament(original_tournament)
        try:
            self.assertIsNotNone(new_tournament.get("tournament_id"))
        finally:
            self.da.delete_tournament(new_tournament.get("tournament_id"))

        # Test an admin creating a valid tournament with a draws_url
        original_tournament["draws_url"] = "../test_empty_draws.html"
        new_tournament = self.manager.create_tournament(original_tournament)
        try:
            self.assertIsNotNone(new_tournament.get("master_bracket_id"))
        finally:
            self.da.delete_tournament(new_tournament.get("tournament_id"))

    def test_scrape_active_tournaments(self):
        tournament = self.da.create_tournament({
            "name": "Test",
            "draws_url": "../test_full_draws.html",
            "start_date": datetime.today().date() + timedelta(days = 1),
            "end_date": datetime.today().date() + timedelta(days = 2)
        })
        try:
            # Test that the tournament has no master bracket yet
            self.assertIsNone(tournament.get("master_bracket_id"))

            # Test as a non-admin
            e = assert_error(lambda: self.manager.scrape_active_tournaments())
            self.assertEqual(403, e.status_code)

            # Test as an admin
            self.become_admin()
            self.manager.scrape_active_tournaments()
            new_tournament = self.da.get_tournament(tournament["tournament_id"])
            self.assertIsNotNone(new_tournament.get("master_bracket_id"))
        finally:
            self.da.delete_tournament(tournament["tournament_id"])

    def test_update_bracket(self):
        tournament_id = self.da.create_tournament({"name": "Test"})["tournament_id"]
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
            master_bracket = self.da.create_bracket({"tournament_id": tournament_id, "name": "Test - Results"})
            self.da.create_match({"bracket_id": master_bracket.get("bracket_id"), "round": 1, "position": 1})
            master_bracket = self.manager.get_bracket(master_bracket.get("bracket_id"))
            test_bracket = self.da.create_bracket({"user_id": self.manager.user["user_id"], "tournament_id": tournament_id, "name": "Test"})
            self.da.create_match({"bracket_id": test_bracket.get("bracket_id"), "round": 1, "position": 1})
            test_bracket = self.manager.get_bracket(test_bracket.get("bracket_id"))

            # Test updating master as non-admin
            e = assert_error(lambda: self.manager.update_bracket(master_bracket.get("bracket_id"), master_bracket))
            self.assertEqual(403, e.status_code)

            # Test updating your bracket as non-admin
            test_bracket["name"] = "New Name"
            new_bracket = self.manager.update_bracket(test_bracket.get("bracket_id"), test_bracket)
            self.assertEqual("New Name", new_bracket.get("name"))

            # Test updating someone else's bracket as admin
            test_bracket["name"] = "Another New Name"
            self.become_admin()
            new_bracket = self.manager.update_bracket(test_bracket.get("bracket_id"), test_bracket)
            self.assertEqual("Another New Name", new_bracket.get("name"))

            # Test updating bracket's rounds
            test_bracket["rounds"][0][0]["player1_id"] = 1
            new_bracket = self.manager.update_bracket(test_bracket.get("bracket_id"), test_bracket)
            self.assertEqual(1, new_bracket["rounds"][0][0].get("player1_id"))

            # Test updating bracket's rounds with unknown player
            test_bracket["rounds"][0][0]["player2_name"] = "Tester"
            new_bracket = self.manager.update_bracket(test_bracket.get("bracket_id"), test_bracket)
            new_player_id = new_bracket["rounds"][0][0].get("player2_id")
            self.assertIsNotNone(new_player_id)

            # Test updating master bracket as admin (no first round changes)
            master_bracket["name"] = "New Name"
            new_bracket = self.manager.update_bracket(master_bracket.get("bracket_id"), master_bracket)
            self.assertEqual("New Name", new_bracket["name"])

            # Test updating master bracket with first round changes that should propogate
            for field in ["player1_id", "player2_id", "seed1", "seed2"]:
                master_bracket["rounds"][0][0][field] = 1
                new_bracket = self.manager.update_bracket(master_bracket.get("bracket_id"), master_bracket)
                self.assertEqual(1, new_bracket["rounds"][0][0].get(field))
                new_bracket = self.manager.get_bracket(test_bracket.get("bracket_id"))
                self.assertEqual(1, new_bracket["rounds"][0][0].get(field))

            # Test updating master bracket with first round changes that shouldn't propogate
            master_bracket["rounds"][0][0]["winner_id"] = 1
            new_bracket = self.manager.update_bracket(master_bracket.get("bracket_id"), master_bracket)
            self.assertEqual(1, new_bracket["rounds"][0][0].get("winner_id"))
            new_bracket = self.manager.get_bracket(test_bracket.get("bracket_id"))
            self.assertNotEqual(1, new_bracket["rounds"][0][0].get("winner_id"))
        finally:
            self.da.delete_tournament(tournament_id)
            if new_player_id is not None:
                self.da.delete_player(new_player_id)

    def test_scrape_master_bracket_draws(self):
        tournament = {"name": "Test"}
        tournament = self.da.create_tournament(tournament)

        try:
            # Test an invalid tournament id
            e = assert_error(lambda: self.manager.scrape_master_bracket_draws(None))
            self.assertEqual(400, e.status_code)

            # Test a tournament without draws
            e = assert_error(lambda: self.manager.scrape_master_bracket_draws(tournament.get("tournament_id")))
            self.assertEqual(412, e.status_code)

            # Test an invalid bracket
            self.become_admin()
            tournament["draws_url"] = "../test_invalid_draws.html"
            tournament = self.da.update_tournament(tournament.get("tournament_id"), tournament)
            e = assert_error(lambda: self.manager.scrape_master_bracket_draws(tournament.get("tournament_id")))
            self.assertEqual(400, e.status_code)

            # Test creating a master bracket
            tournament["draws_url"] = "../test_empty_draws.html"
            tournament = self.da.update_tournament(tournament.get("tournament_id"), tournament)
            master_bracket = self.manager.scrape_master_bracket_draws(tournament.get("tournament_id"))
            self.assertEqual(master_bracket["rounds"], [])

            # Test updating a master bracket
            master_bracket = self.manager.scrape_master_bracket_draws(tournament.get("tournament_id"))
            self.assertEqual(master_bracket["rounds"], [])
        finally:
            self.da.delete_tournament(tournament.get("tournament_id"))

def assert_error(statement):
    try:
        statement()
        assert False
    except ServiceException as e:
        return e
