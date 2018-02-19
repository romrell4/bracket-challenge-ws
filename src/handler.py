import json

from manager import Manager
from service_exception import ServiceException
from da import Dao
import auth
from res import properties

da = Dao()

def lambda_handler(event, context):
    try:
        if event is None:
            raise ServiceException("Invalid request", 400)

        if "scraper" in event:
            print("Running scraper")
            Manager(da, properties.admin_username).scrape_active_tournaments()
            return

        if "resource" not in event or "httpMethod" not in event:
            raise ServiceException("Invalid request. No 'resource', or 'httpMethod' found in event", 400)

        resource, method = event["resource"], event["httpMethod"]  # These will be used to specify which endpoint was being hit
        path_parameters = event.get("pathParameters", {}) if event.get("pathParameters") is not None else {}  # This will be used to get IDs and other parameters from the URL
        query_parameters = event.get("queryStringParameters", {}) if event.get("queryStringParameters") is not None else {}
        try:
            body = json.loads(event["body"])  # This will be used for most POSTs and PUTs
        except (TypeError, KeyError, ValueError):
            body = None

        fb_user = auth.validate_user(event)

        manager = Manager(da, fb_user["email"])

        # Find the endpoint they are hitting, and process the request
        if resource == "/users" and method == "POST":
            response_body = manager.login(fb_user)
        elif manager.user is None:
            # If this user isn't in our database, they are only allowed to use the login endpoint
            raise ServiceException("This user is not tracked in our database. The only allowed endpoint is /users POST to create an account.", 403)
        elif resource == "/players" and method == "GET":
            response_body = manager.get_players()
        elif resource == "/tournaments" and method == "GET":
            response_body = manager.get_tournaments()
        elif resource == "/tournaments" and method == "POST":
            response_body = manager.create_tournament(body)
        elif resource == "/tournaments/{tournamentId}" and method == "GET":
            response_body = manager.get_tournament(path_parameters.get("tournamentId"))
        elif resource == "/tournaments/{tournamentId}" and method == "PUT":
            response_body = manager.update_tournament(path_parameters.get("tournamentId"), body)
        elif resource == "/tournaments/{tournamentId}/scrape" and method == "POST":
            response_body = manager.scrape_master_bracket_draws(path_parameters.get("tournamentId"))
        elif resource == "/tournaments/{tournamentId}/brackets" and method == "GET":
            response_body = manager.get_brackets(path_parameters.get("tournamentId"))
        elif resource == "/tournaments/{tournamentId}/brackets" and method == "POST":
            response_body = manager.create_bracket(path_parameters.get("tournamentId"), body)
        elif resource == "/tournaments/{tournamentId}/brackets/mine":
            response_body = manager.get_my_bracket(path_parameters.get("tournamentId"))
        elif resource == "/tournaments/{tournamentId}/brackets/{bracketId}" and method == "GET":
            response_body = manager.get_bracket(path_parameters.get("bracketId"))
        elif resource == "/tournaments/{tournamentId}/brackets/{bracketId}" and method == "PUT":
            response_body = manager.update_bracket(path_parameters.get("bracketId"), body)
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
