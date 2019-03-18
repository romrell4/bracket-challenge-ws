import re
from datetime import datetime
from urllib.parse import urljoin

import bs4
import requests
from bs4 import BeautifulSoup

PLAYER_DICT = {}

def scrape_tournaments(tournaments_url, existing_tournaments, today = datetime.now()):
    html = get_html(tournaments_url)
    rows = html.find_all("tr", "tourney-result")

    new_tournaments = []

    for row in rows:
        try: new_tournaments.append(get_tournament(tournaments_url, row, existing_tournaments, today))
        except Exception as e: print(e)

    return new_tournaments

def get_tournament(base_url, row, existing_tournaments, today = datetime.utcnow()):
    name = row.find("span", "tourney-location").text.strip().split(",")[0]
    start_date, end_date = [datetime.strptime(value, "%Y.%m.%d") for value in row.find("span", "tourney-dates").text.strip().split(" - ")]
    day_diff = (start_date - today).days
    if day_diff >= 2:
        raise InvalidTournamentException(name, "Tournament is too far in the future.")
    elif day_diff < 0:
        raise InvalidTournamentException(name, "Tournament has already started.")

    singles_players = int(row.find("td", "tourney-details").find("span", "item-value").text.strip())
    if singles_players < 16:
        raise InvalidTournamentException(name, "Too few singles players. Most likely not a valid tournament.")

    if next((t for t in existing_tournaments if t["name"] == name and datetime.strptime(t["start_date"], "%Y-%m-%d") == start_date), None) is not None:
        raise InvalidTournamentException(name, "Tournament already exists.")

    overview_url = urljoin(base_url, row.find("a", "tourney-title").attrs.get("href"))
    html = get_html(overview_url)

    draws_url = urljoin(overview_url, html.find("li", id = "draw_SectionLink").find("a").attrs["href"])

    if "archive" in draws_url:
        raise InvalidTournamentException(name, "Tournament draws are not published yet.")

    image_style = html.find("div", id = "tournamentHero").attrs["style"]
    image_url = urljoin(overview_url, re.match("background-image:url\('(.*)'\)", image_style).group(1))

    return {
        "name": name,
        "start_date": start_date,
        "end_date": end_date,
        "draws_url": draws_url,
        "image_url": image_url
    }

def scrape_bracket(draws_url, all_players = None):
    for player in all_players if all_players is not None else []:
        PLAYER_DICT[player["name"]] = player["player_id"]

    # If the draw looks like a valid URL, make a request to get it. Otherwise, it's a test, and load it from a local file
    html = get_html(draws_url)
    table = html.find("table", id = "scoresDrawTable")

    if table is None:
        return None

    def get_name(tag):
        link = tag.find("a", "scores-draw-entry-box-players-item")
        return link["data-ga-label"] if link is not None else None

    def get_seed(tag):
        try: return int(re.sub(r"\D", "", tag.find("span").string))
        except: return None

    seeds = {}
    rounds = [[] for _ in table.thead.tr.find_all("th")]
    for row in list([row for row in table.tbody.children if isinstance(row, bs4.element.Tag)]):
        for round, round_td in enumerate([td for td in list(row.children) if isinstance(td, bs4.element.Tag)]):
            if round == 0:
                match_trs = round_td.find_all("tr")
                player1_name = get_name(match_trs[0])
                player2_name = get_name(match_trs[1])
                rounds[round] += [player1_name, player2_name]

                seeds[player1_name] = get_seed(match_trs[0])
                seeds[player2_name] = get_seed(match_trs[1])
            else:
                player_name = get_name(round_td)
                rounds[round].append(player_name)

    bracket = []
    for round, players in enumerate(rounds[:-1]):
        bracket.append([])
        for i in range(0, len(players), 2):
            player1, player2 = players[i], players[i + 1]
            seed1, seed2 = seeds[player1] if player1 in seeds else None, seeds[player2] if player2 in seeds else None
            winner_name = rounds[round + 1][int(i / 2)]
            match = Match(round + 1, int(i / 2) + 1, player1, player2, seed1, seed2, winner_name)
            bracket[round].append(match.__dict__)
    return {"rounds": bracket}

class Match:
    def __init__(self, round, position, player1_name = None, player2_name = None, seed1 = None, seed2 = None, winner_name = None):
        self.round = round
        self.position = position
        self.set_player_info(player1_name, seed1, "1")
        self.set_player_info(player2_name, seed2, "2")
        winner_id = self.find_id(winner_name)
        if winner_id is not None:
            self.winner_id = winner_id

    def set_player_info(self, name, seed, position):
        if name is not None and name != "":
            player_id = self.find_id(name)
            if player_id is not None:
                setattr(self, "player{}_id".format(position), player_id)
            else:
                setattr(self, "player{}_name".format(position), name)
        if seed is not None:
            setattr(self, "seed{}".format(position), seed)

    @staticmethod
    def find_id(player_name):
        return PLAYER_DICT[player_name] if player_name in PLAYER_DICT else None

def get_html(url):
    # If the url looks like a valid URL, make a request to get it. Otherwise, it's a test, and load it from a local file
    if url.startswith("http"):
        html = requests.get(url).text
    else:
        if url.startswith("/en"):
            url = "../tournaments/{}.html".format(url.split("/")[3])
        with open(url) as f:
            html = f.read()

    return BeautifulSoup(html, "html.parser")

class InvalidTournamentException(Exception):
    def __init__(self, name, message):
        self.message = "Skipping '{}'. {}".format(name, message)
