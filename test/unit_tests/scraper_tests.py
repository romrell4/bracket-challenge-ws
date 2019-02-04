from unittest import TestCase
from bs4 import BeautifulSoup

from da import Dao
import scraper
from datetime import datetime

class ScraperTests(TestCase):
    def test_scrape_tournaments(self):
        new_tournaments = scraper.scrape_tournaments("../tournaments.html", [], datetime(2019, 2, 1))
        self.assertEqual(3, len(new_tournaments))

    def test_get_tournament(self):
        def test(today, html_file = "../tournament_row.html", existing_tournaments = []):
            with open(html_file) as f: row = BeautifulSoup(f.read(), "html.parser")
            try:
                return scraper.get_tournament("", row, existing_tournaments, today)
            except scraper.InvalidTournamentException as e:
                return e

        # Test if the tournament is in the future
        exception = test(datetime(2019, 1, 31))
        self.assertEqual("Skipping 'Cordoba'. Tournament is too far in the future.", exception.message)

        # Test if the tournament is in the past
        exception = test(datetime(2019, 2, 5))
        self.assertEqual("Skipping 'Cordoba'. Tournament has already started.", exception.message)

        # Test if the tournament is not a valid one (Davis Cup)
        exception = test(datetime(2019, 2, 1), "../tournament_row_davis_cup.html")
        self.assertEqual("Skipping 'Multiple Locations'. Too few singles players. Most likely not a valid tournament.", exception.message)

        # Test if the tournament is not a valid one (World Tour Finals)
        exception = test(datetime(2019, 11, 8), "../tournament_row_atp_finals.html")
        self.assertEqual("Skipping 'London'. Too few singles players. Most likely not a valid tournament.", exception.message)

        # Test if the tournament already exists
        exception = test(datetime(2019, 2, 2), existing_tournaments = [{"name": "Cordoba", "start_date": datetime(2019, 2, 4)}])
        self.assertEqual("Skipping 'Cordoba'. Tournament already exists.", exception.message)

        tournament = test(datetime(2019, 2, 2))
        self.assertEqual("Cordoba", tournament["name"])
        self.assertEqual(datetime(2019, 2, 4), tournament["start_date"])
        self.assertEqual(datetime(2019, 2, 10), tournament["end_date"])
        self.assertEqual("/en/scores/current/cordoba/9158/draws", tournament["draws_url"])
        self.assertEqual("/en/tournaments/cordoba/9158/-/media/images/news/2018/12/17/23/28/cordoba-2019-campaign.jpg", tournament["image_url"])

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
            self.assertIsNotNone(match.get("player1_id"))
            self.assertIsNotNone(match.get("player2_id"))

    def test_finished_bracket(self):
        bracket = scraper.scrape_bracket("../test_finished_bracket.html", Dao().get_players())
        self.assertIsNotNone(bracket.get("rounds")[4][0].get("winner_id"))

    def test_walkover(self):
        bracket = scraper.scrape_bracket("../test_walkover.html", Dao().get_players())
        self.assertIsNotNone(bracket.get("rounds")[1][2].get("winner_id"))