import json

from manager import Manager
import auth
from service_exception import ServiceException

def lambda_handler(event, context):
    try:
        if event is None or "resource" not in event or "httpMethod" not in event:
            raise ServiceException("Invalid request. No 'resource', or 'httpMethod' found in event", 400)

        resource, method = event["resource"], event["httpMethod"] # These will be used to specify which endpoint was being hit
        path_parameters = event["pathParameters"] if "pathParameters" in event and event["pathParameters"] is not None else {} # This will be used to get IDs and other parameters from the URL
        query_parameters = event["queryStringParameters"] if "queryStringParameters" in event and event["queryStringParameters"] is not None else {}
        try:
            body = json.loads(event["body"]) # This will be used for most POSTs and PUTs
        except:
            body = None

        fb_user = auth.validate_user(event)

        manager = Manager(fb_user["email"])

        # Find the endpoint they are hitting, and process the request
        if resource == "/users" and method == "POST":
            response_body = manager.login(fb_user)
        elif manager.user is None:
            # If this user isn't in our database, they are only allowed to use the login endpoint
            raise ServiceException("This user is not tracked in our database. The only allowed endpoint is /users POST to create an account.", 403)
        elif resource == "/tournaments" and method == "GET":
            response_body = manager.get_tournaments()
        elif resource == "/tournaments/{tournamentId}/brackets" and method == "GET":
            mine = "mine" in query_parameters and query_parameters["mine"] == "true"
            response_body = manager.get_brackets(path_parameters["tournamentId"], mine)
        elif resource == "/tournaments/{tournamentId}/brackets/{bracketId}" and method == "GET":
            response_body = manager.get_bracket(path_parameters["bracketId"])
        else:
            raise ServiceException("Invalid path: '{} {}'".format(resource, method))

        return format_response(response_body)
    except ServiceException as e:
        print(e.error_message)
        return format_response({"error": e.error_message}, e.status_code)

def format_response(body = None, status_code = 200):
    return {
        "statusCode": status_code,
        "body": json.dumps(body) if body is not None else None
    }
