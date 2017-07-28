import sys
import properties
import pymysql

rds_host = properties.db_host
name = properties.db_username
password = properties.db_password
db_name = properties.db_name

try:
    conn = pymysql.connect(rds_host, user = name, passwd = password, db = db_name, connect_timeout = 5)
except Exception as e:
    print("ERROR: Could not connect to MySQL", e)
    sys.exit()

def get_brackets():
    get_list("select * from brackets")

def get_bracket(bracket_id):
    get_one("select * from brackets where bracket_id = {}".format(bracket_id))

def get_tournaments():
    get_list("select * from tournaments")

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
