import unittest

import da

class DaTest(unittest.TestCase):
    def test_users(self):
        dict1 = {"username": "test", "name": "test"}
        dict2 = {"username": "test", "name": "test2"}
        self.run_simple_tests(da.get_users, da.create_user, da.update_user, da.delete_user, "user_id", dict1, dict2)

    def test_players(self):
        dict1 = {"name": "test"}
        dict2 = {"name": "test2"}
        self.run_simple_tests(da.get_players, da.create_player, da.update_player, da.delete_player, "player_id", dict1, dict2)

    def test_tournaments(self):
        dict1 = {"name": "test"}
        dict2 = {"name": "test", "master_bracket_id": 0}
        self.run_simple_tests(da.get_tournaments, da.create_tournament, da.update_tournament, da.delete_tournament, "tournament_id", dict1, dict2)

    def test_brackets(self):
        dict1 = {"user_id": 0, "tournament_id": 0, ""}
        dict2 = {""}
        self.run_simple_tests(da.get_brackets, da.create_bracket, da.update_bracket, da.delete_bracket, "bracket_id", dict1, dict2)

    @staticmethod
    def run_simple_tests(get_all, create, update, delete, id_key, create_dict, update_dict):
        # Test get all
        objs = get_all()
        assert objs is not None

        # Test create (which also tests get)
        obj = create(create_dict)
        obj_id = None
        try:
            assert obj is not None
            obj_id = obj[id_key]

            # Test update
            new_obj = update(obj_id, update_dict)
            assert obj != new_obj
        finally:
            if obj_id is not None:
                # Test delete
                delete(obj_id)

