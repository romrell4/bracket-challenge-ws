import requests
import bs4
from bs4 import BeautifulSoup
import re

import da

PLAYER_DICT = {}

# Public method. This is the only one that should be called outside of this file
def scrape_bracket(draws_url):
    for player in da.get_players():
        PLAYER_DICT[player["name"]] = player["player_id"]

    # If the draw looks like a valid URL, make a request to get it. Otherwise, it's a test, and load it from a local file
    if draws_url.startswith("http"):
        html = requests.get(draws_url).text
    else:
        with open(draws_url) as f: html = f.read()

    soup = BeautifulSoup(html, "html.parser")
    table = soup.find("table", id = "scoresDrawTable")

    seeds = {}
    rounds = [[] for _ in table.thead.tr.find_all("th")]
    for row in list([row for row in table.tbody.children if isinstance(row, bs4.element.Tag)]):
        for round, round_td in enumerate([td for td in list(row.children) if isinstance(td, bs4.element.Tag)]):
            if round == 0:
                match_trs = round_td.find_all("tr")
                player1_name = _get_name(match_trs[0])
                player2_name = _get_name(match_trs[1])
                rounds[round] += [player1_name, player2_name]

                seeds[player1_name] = _get_seed(match_trs[0])
                seeds[player2_name] = _get_seed(match_trs[1])
            else:
                player_name = _get_name(round_td)
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

def _get_seed(tag):
    return re.sub(r"\D", "", tag.find("span").string) if tag.find("span") else None

def _get_name(tag):
    link = tag.find("a", "scores-draw-entry-box-players-item")
    return link['data-ga-label'] if link is not None else None

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
        if seed is not None and seed != "":
            setattr(self, "seed{}".format(position), seed)

    @staticmethod
    def find_id(player_name):
        return PLAYER_DICT[player_name] if player_name in PLAYER_DICT else None
