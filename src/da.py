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
    return get_list(User, "SELECT * FROM users")

def get_user(user_id):
    return get_one(User, "SELECT * FROM users WHERE user_id = %s", user_id)

def get_user_by_username(username):
    return get_one(User, "SELECT * FROM users WHERE username = %s", username)

def create_user(user):
    user_id = insert("INSERT INTO users (username, name) VALUES (%s, %s)", user.get("username"), user.get("name"))
    return get_user(user_id)

def update_user(user_id, user):
    execute("UPDATE users SET username = %s, name = %s WHERE user_id = %s", user.get("username"), user.get("name"), user_id)
    return get_user(user_id)

def delete_user(user_id):
    execute("DELETE FROM users WHERE user_id = %s", user_id)
    return None

### PLAYERS ###

def get_players():
    return get_list(Player, "SELECT * FROM players")

def get_player(player_id):
    return get_one(Player, "SELECT * FROM players WHERE player_id = %s", player_id)

def create_player(player):
    player_id = insert("INSERT INTO players (name) VALUES (%s)", player.get("name"))
    return get_player(player_id)

def create_players(players):
    sql = "INSERT INTO players (name) VALUES "
    values = []
    args = []
    for player in players:
        values.append("(%s)")
        args.append(player.get("name"))
    sql += ", ".join(values)
    execute(sql, *args)

def update_player(player_id, player):
    execute("UPDATE players SET name = %s WHERE player_id = %s", player.get("name"), player_id)
    return get_player(player_id)

def delete_player(player_id):
    execute("DELETE FROM players WHERE player_id = %s", player_id)

### TOURNAMENTS ###

def get_tournaments():
    return get_list(Tournament, "SELECT * FROM tournaments")

def get_tournament(tournament_id):
    return get_one(Tournament, "SELECT * FROM tournaments WHERE tournament_id = %s", tournament_id)

def create_tournament(tournament):
    if "active" not in tournament:
        tournament["active"] = 0
    tournament_id = insert("INSERT INTO tournaments (name, master_bracket_id, image_url, active) VALUES (%s, %s, %s, %s)", tournament.get("name"), tournament.get("master_bracket_id"), tournament.get("image_url"), tournament.get("active"))
    return get_tournament(tournament_id)

def update_tournament(tournament_id, tournament):
    execute("UPDATE tournaments SET name = %s, master_bracket_id = %s, image_url = %s, active = %s WHERE tournament_id = %s", tournament.get("name"), tournament.get("master_bracket_id"), tournament.get("image_url"), tournament.get("active"), tournament_id)
    return get_tournament(tournament_id)

def delete_tournament(tournament_id):
    execute("DELETE FROM tournaments WHERE tournament_id = %s", tournament_id)

### BRACKETS ###

def get_brackets(tournament_id):
    return get_list(Bracket, "SELECT * FROM brackets WHERE tournament_id = %s", tournament_id)

def get_bracket(bracket_id = None, tournament_id = None, user_id = None):
    if bracket_id is not None:
        return get_one(Bracket, "SELECT * FROM brackets WHERE bracket_id = %s", bracket_id)
    elif tournament_id is not None and user_id is not None:
        return get_one(Bracket, "SELECT * FROM brackets WHERE tournament_id = %s AND user_id = %s", tournament_id, user_id)
    return None

def create_bracket(bracket):
    bracket_id = insert("INSERT INTO brackets (user_id, tournament_id, name) VALUES (%s, %s, %s)", bracket.get("user_id"), bracket.get("tournament_id"), bracket.get("name"))
    return get_bracket(bracket_id)

def update_bracket(bracket_id, bracket):
    execute("UPDATE brackets SET user_id = %s, tournament_id = %s, name = %s WHERE bracket_id = %s",
            bracket.get("user_id"), bracket.get("tournament_id"), bracket.get("name"), bracket_id)
    return get_bracket(bracket_id)

def delete_bracket(bracket_id):
    execute("DELETE FROM brackets WHERE bracket_id = %s", bracket_id)

### MATCHES ###

def get_matches(bracket_id):
    return get_list(MatchHelper, """
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
        WHERE bracket_id = %s
        ORDER BY round, position""", bracket_id)

def get_match(match_id):
    return get_one(Match, "SELECT * FROM matches WHERE match_id = %s", match_id)

def create_match(match):
    match_id = insert("INSERT INTO matches (bracket_id, round, position, player1_id, player2_id, seed1, seed2, winner_id) VALUES (%s, %s, %s, %s, %s, %s, %s, %s)",
                      match.get("bracket_id"), match.get("round"), match.get("position"), match.get("player1_id"), match.get("player2_id"), match.get("seed1"), match.get("seed2"), match.get("winner_id"))
    return get_match(match_id)

def create_matches(bracket_id, rounds):
    sql = "INSERT INTO matches (bracket_id, round, position, player1_id, player2_id, seed1, seed2, winner_id) VALUES "
    values = []
    args = []
    for round in rounds:
        for match in round:
            values.append("(%s, %s, %s, %s, %s, %s, %s, %s)")
            args += [bracket_id, match.get("round"), match.get("position"), match.get("player1_id"), match.get("player2_id"), match.get("seed1"), match.get("seed2"), match.get("winner_id")]
    sql += ", ".join(values)
    execute(sql, *args)

def update_match(match_id, match):
    execute("UPDATE matches SET bracket_id = %s, round = %s, position = %s, player1_id = %s, player2_id = %s, seed1 = %s, seed2 = %s, winner_id = %s where match_id = %s",
            match.get("bracket_id"), match.get("round"), match.get("position"), match.get("player1_id"), match.get("player2_id"), match.get("seed1"), match.get("seed2"), match.get("winner_id"), match_id)
    return get_match(match_id)

def delete_match(match_id):
    execute("DELETE FROM matches WHERE match_id = %s", match_id)

### SCORES ###

def get_score(bracket_id):
    return int(get_one(Score, """select SUM(match_scores.score) from (
        select IF(my_m.winner_id = ma_m.winner_id, 1, 0) * my_m.round as score
        from matches my_m
        join brackets my_b
            on my_m.bracket_id = my_b.bracket_id
        join tournaments t
            on t.tournament_id = my_b.tournament_id
        join brackets ma_b
            on t.master_bracket_id = ma_b.bracket_id
        join matches ma_m
            on ma_m.bracket_id = ma_b.bracket_id
            and my_m.position = ma_m.position
            and my_m.round = ma_m.round
        where my_m.bracket_id = %s
        ) match_scores""", bracket_id)["score"])

### UTILS ###

def get_list(klass, sql, *args):
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            results = []
            for row in cur.fetchall():
                results.append(klass(row).__dict__)
            return results
    except Exception as e:
        print(e)
        raise ServiceException("Error getting data from database")

def get_one(klass, sql, *args):
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            result = cur.fetchone()
            if result is not None:
                return klass(result).__dict__
            return None
    except Exception as e:
        print(e)
        raise ServiceException("Error getting data from database")

def insert(sql, *args):
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
            return cur.lastrowid
    except Exception as e:
        print(e)
        raise ServiceException("Error inserting data into database")

def execute(sql, *args):
    try:
        with conn.cursor() as cur:
            cur.execute(sql, args)
    except Exception as e:
        print(e)
        raise ServiceException("Error executing database command")
