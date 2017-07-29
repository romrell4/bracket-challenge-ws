import sys

import pymysql
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
    return get_list("SELECT * FROM users")

def get_user(user_id):
    return get_one("SELECT * FROM users WHERE user_id = {}".format(user_id))

def create_user(user):
    user_id = insert("INSERT INTO users (username, name) VALUES ({}, {})".format(user["username"], user["name"]))
    return get_user(user_id)

def update_user(user_id, user):
    execute("UPDATE users SET username = {}, name = {} WHERE user_id = {}".format(user["username"], user["name"], user_id))
    return get_user(user_id)

def delete_user(user_id):
    execute("DELETE FROM users WHERE user_id = {}".format(user_id))
    return None # TODO

### PLAYERS ###

def get_players():
    return None

def get_player(player_id):
    return None # TODO

def create_player(player):
    return None # TODO

def update_player(player_id, player):
    return None # TODO

def delete_player(player_id):
    return None # TODO

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

def get_list(sql):
    with conn.cursor() as cur:
        cur.execute(sql)
        results = []
        for row in cur.fetchall():
            results.append(row)
        return results

def get_one(sql):
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.fetchone()

def insert(sql):
    with conn.cursor() as cur:
        cur.execute(sql)
        return cur.lastrowid

def execute(sql):
    with conn.cursor() as cur:
        cur.execute(sql)
