import sys
import pymysql

from model import *
from service_exception import ServiceException

from res import properties

rds_host = properties.db_host
name = properties.db_username
password = properties.db_password
db_name = properties.db_name

try:
    conn = pymysql.connect(rds_host, user = name, passwd = password, db = db_name, autocommit = True)
except Exception as e:
    print("ERROR: Could not connect to MySQL", e)
    sys.exit()

### USERS ###

def get_users():
    return get_list("SELECT * FROM users", User)

def get_user(user_id):
    return get_one("SELECT * FROM users WHERE user_id = {}".format(user_id), User)

def get_user_by_username(username):
    return get_one("SELECT * FROM users WHERE username = '{}'".format(username), User)

def create_user(user):
    user_id = insert("INSERT INTO users (username, name) VALUES ('{}', '{}')".format(user["username"], user["name"]))
    return get_user(user_id)

def update_user(user_id, user):
    execute("UPDATE users SET username = '{}', name = '{}' WHERE user_id = {}".format(user["username"], user["name"], user_id))
    return get_user(user_id)

def delete_user(user_id):
    execute("DELETE FROM users WHERE user_id = {}".format(user_id))
    return None

### PLAYERS ###

def get_players():
    return get_list("SELECT * FROM players", Player)

def get_player(player_id):
    return get_one("SELECT * FROM players WHERE player_id = {}".format(player_id), Player)

def create_player(player):
    player_id = insert("INSERT INTO players (name) VALUES ('{}')".format(player["name"]))
    return get_player(player_id)

def update_player(player_id, player):
    execute("UPDATE players SET name = '{}' WHERE player_id = {}".format(player["name"], player_id))
    return get_player(player_id)

def delete_player(player_id):
    execute("DELETE FROM players WHERE player_id = {}".format(player_id))

### TOURNAMENTS ###

def get_tournaments():
    return get_list("SELECT * FROM tournaments", Tournament)

def get_tournament(tournament_id):
    return get_one("SELECT * FROM tournaments WHERE tournament_id = {}".format(tournament_id))

def create_tournament(tournament):
    # TODO: Fix KeyError if master_bracket_id is not provided
    tournament_id = insert("INSERT INTO tournaments (name, master_bracket_id) VALUES ('{}', {})".format(tournament["name"], tournament["master_bracket_id"]))
    return get_tournament(tournament_id)

def update_tournament(tournament_id, tournament):
    # TODO: Fix KeyError if master_bracket_id is not provided
    execute("UPDATE tournaments SET name = '{}', master_bracket_id = {} WHERE tournament_id = {}".format(tournament["name"], tournament["master_bracket_id"], tournament_id))
    return get_tournament(tournament_id)

def delete_tournament(tournament_id):
    execute("DELETE FROM tournaments WHERE tournament_id = {}".format(tournament_id))

### BRACKETS ###

def get_brackets():
    return get_list("SELECT * FROM brackets", Bracket)

def get_bracket(bracket_id):
    return get_one("SELECT * FROM brackets WHERE bracket_id = {}".format(bracket_id), Bracket)

def create_bracket(bracket):
    return None # TODO

def update_bracket(bracket_id, bracket):
    return None # TODO

def delete_bracket(bracket_id):
    return None # TODO

### MATCHES ###

def get_matches(bracket_id):
    return get_list("""
        SELECT m.match_id, m.bracket_id, m.round, m.position,
          m.player1_id, p1.name as player1_name,
          m.player2_id, p2.name as player2_name,
          m.seed1, m.seed2, m.winner_id, w.name as winner_name
        FROM matches m
        LEFT JOIN players p1
          on m.player1_id = p1.player_id
        LEFT JOIN players p2
          on m.player2_id = p2.player_id
        LEFT JOIN players w
          on m.winner_id = w.player_id
        WHERE bracket_id = {}
        ORDER BY round, position""".format(bracket_id), MatchHelper)

def create_match(match):
    return None # TODO

def update_match(match_id, match):
    return None # TODO

def delete_match(match_id):
    return None # TODO

### UTILS ###

def get_list(sql, klass):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            results = []
            for row in cur.fetchall():
                results.append(klass(row).__dict__)
            return results
    except Exception as e:
        print(e)
        raise ServiceException("Error getting data from database")

def get_one(sql, klass):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            result = cur.fetchone()
            if result is not None:
                return klass(result).__dict__
            return None
    except Exception as e:
        print(e)
        raise ServiceException("Error getting data from database")

def insert(sql):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
            return cur.lastrowid
    except Exception as e:
        print(e)
        raise ServiceException("Error inserting data into database")

def execute(sql):
    try:
        with conn.cursor() as cur:
            cur.execute(sql)
    except Exception as e:
        print(e)
        raise ServiceException("Error executing database command")
