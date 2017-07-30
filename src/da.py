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
    return None

### TOURNAMENTS ###

def get_tournaments():
    return None # TODO

def get_tournament(tournament_id):
    return None # TODO

def create_tournament(tournament):
    return None # TODO

def update_tournament(tournament_id, tournament):
    return None # TODO

def delete_tournament(tournament_id):
    return None # TODO

### BRACKETS ###

def get_brackets():
    return get_list("SELECT * FROM brackets")

def get_bracket(bracket_id):
    return None # TODO

def create_bracket(bracket):
    return None # TODO

def update_bracket(bracket_id, bracket):
    return None # TODO

def delete_bracket(bracket_id):
    return None # TODO

### MATCHES ###

def get_matches():
    return None # TODO

def get_match(match_id):
    return None # TODO

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
            return klass(cur.fetchone()).__dict__
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
