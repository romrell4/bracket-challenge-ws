from service_exception import ServiceException
from manager import Manager

import json
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

def lambda_handler(event, context):
    try:
        if "resource" not in event or "httpMethod" not in event:
            raise ServiceException("Invalid request. No 'resource' or 'httpMethod' found in event", 400)

        resource, method = event["resource"], event["httpMethod"] # These will be used to specify which endpoint was being hit
        path_parameters = event["pathParameters"] # This will be used to get IDs and other parameters from the URL

        manager = Manager()

        if resource == "/brackets":
            if method == "GET":
                response_body = manager.get_brackets()
            elif method == "POST":
                # TODO: Parse request body and pass into create_bracket
                response_body = manager.create_bracket()

        # TODO: Fill in more endpoints here

        else:
            raise ServiceException("Invalid path: '{} {}'".format(resource, method))

        return format_response(response_body)
    except ServiceException as e:
        return format_response({"error": e.error_message}, e.status_code)

def format_response(body = None, status_code = 200):
    return {
        "statusCode": status_code,
        "body": json.dumps(body) if body is not None else None
    }
