from unittest2 import TestCase

from da import Dao
import scraper

class ScraperTests(TestCase):
    def test_scrape_bracket(self):
        # Test an invalid draw
        bracket = scraper.scrape_bracket("../test_invalid_draws.html")
        self.assertIsNone(bracket)

        # Test an empty draw
        bracket = scraper.scrape_bracket("../test_empty_draws.html")
        self.assertEqual([], bracket.get("rounds"))

        # Load up all the players
        players = Dao().get_players()

        # Test a draw still missing some slots, but with a mostly filled out first round
        bracket = scraper.scrape_bracket("../test_new_draws.html", players)
        self.assertEqual(5, len(bracket.get("rounds")))
        self.assertEqual(1, bracket.get("rounds")[0][0].get("player1_id")) # Player ID look up test
        self.assertEqual(1, bracket.get("rounds")[0][0].get("seed1")) # Seed test
        self.assertIsNone(bracket.get("rounds")[0][0].get("player2_id")) # Qualifier test
        self.assertEqual({"round": 2, "position": 1}, bracket.get("rounds")[1][0]) # Empty test

        bracket = scraper.scrape_bracket("../test_partial_draws.html", players)
        self.assertEqual(5, len(bracket.get("rounds")))
        self.assertEqual(6894, bracket.get("rounds")[0][0].get("player1_id"))
        self.assertIsNone(bracket.get("rounds")[0][0].get("player2_id")) # Bye test
        self.assertEqual(6894, bracket.get("rounds")[0][0].get("winner_id")) # Winner test

        bracket = scraper.scrape_bracket("../test_full_draws.html")
        self.assertEqual(7, len(bracket.get("rounds")))

    def test_french(self):
        bracket = scraper.scrape_bracket("../test_french_open.html")
        self.assertEqual(7, len(bracket.get("rounds")))
        for match in bracket.get("rounds")[0]:
            self.assertIsNotNone(match.get("player1_name"))
            self.assertIsNotNone(match.get("player2_name"))

    def test_finished_bracket(self):
        bracket = scraper.scrape_bracket("../test_finished_bracket.html", Dao().get_players())
        self.assertIsNotNone(bracket.get("rounds")[4][0].get("winner_id"))

    def test_walkover(self):
        bracket = scraper.scrape_bracket("../test_walkover.html", Dao().get_players())
        self.assertIsNotNone(bracket.get("rounds")[1][2].get("winner_id"))