import sys
import properties
import pymysql

from model import Bracket

rds_host = properties.db_host
name = properties.db_username
password = properties.db_password
db_name = properties.db_name

BRACKET_QUERY = """
    select u.name, t.name, b.name, m.round, m.position, p1.name, p2.name, w.name
    from brackets b
    join matches m
        on b.bracket_id = m.bracket_id
    join users u
        on b.user_id = u.user_id
    join tournaments t
        on b.tournament_id = t.tournament_id
    join players p1
        on m.player1_id = p1.player_id
    join players p2
        on m.player2_id = p2.player_id
    join players w
        on m.winner_id = w.player_id
    where m.bracket_id = 2
    order by round, position
"""

try:
    conn = pymysql.connect(rds_host, user = name, passwd = password, db = db_name, connect_timeout = 5)
except Exception as e:
    print("ERROR: Could not connect to MySQL", e)
    sys.exit()

def get_brackets():
    return get_list("select * from brackets")

def get_bracket(bracket_id):
    return Bracket(get_list(BRACKET_QUERY.format(bracket_id))).to_dict()

def get_tournaments():
    return get_list("select * from tournaments")

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
