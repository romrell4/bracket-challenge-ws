import json

from manager import Manager
from res import properties
from service_exception import ServiceException

def lambda_handler(event, context):
    try:
        if event is None or "headers" not in event or "resource" not in event or "httpMethod" not in event:
            raise ServiceException("Invalid request. No 'headers', 'resource', or 'httpMethod' found in event", 400)

        auth = event["headers"]["Authorization"]
        if not properties.validate(auth):
            raise ServiceException("Unauthorized. Provided authentication did not validate", 403)

        resource, method = event["resource"], event["httpMethod"] # These will be used to specify which endpoint was being hit
        path_parameters = event["pathParameters"] # This will be used to get IDs and other parameters from the URL
        body = event["body"] # This will be used for most POSTs and PUTs

        manager = Manager()

        if resource == "/users":
            if method == "GET":
                # TODO: parse path parameters
                response_body = manager.get_users()
            elif method == "POST":
                # TODO: PARSE
                response_body = manager.create_user()
            else:
                raise ServiceException("Invalid path: '{} {}'".format(resource, method))

        elif resource == "/users/{userId}":
            if method == "GET":
                #TODO: PARSE
                response_body = manager.get_user()
            elif method == "PUT":
                #TODO: PARSE
                response_body = manager.edit_user()
            elif method == "DELETE":
                #TODO: PARSE
                response_body = manager.delete_user()
            else:
                raise ServiceException("Invalid path: '{} {}'".format(resource, method))

        elif resource == "/players":
            if method == "GET":
                #TODO: PARSE
                response_body = manager.get_players()
            elif method == "POST":
                #TODO: PARSE
                response_body = manager.create_player()
            else:
                raise ServiceException("Invalid path: '{} {}'".format(resource, method))

        elif resource == "/players/{playerId}":
            if method == "GET":
                #TODO: PARSE
                response_body = manager.get_player()
            elif method == "PUT":
                #TODO: PARSE
                response_body = manager.edit_player()
            elif method == "DELETE":
                #TODO: PARSE
                response_body = manager.delete_player()
            else:
                raise ServiceException("Invalid path: '{} {}'".format(resource, method))

        elif resource == "/tournaments":
            if method == "GET":
                #TODO: PARSE
                response_body = manager.get_tournaments()
            elif method == "POST":
                #TODO: PARSE
                response_body = manager.create_tournament()
            else:
                raise ServiceException("Invalid path: '{} {}'".format(resource, method))

        elif resource == "/tournaments/{tournamentId}":
            if method == "GET":
                #TODO: PARSE
                response_body = manager.get_tournament()
            elif method == "PUT":
                #TODO: PARSE
                response_body = manager.edit_tournament()
            elif method == "DELETE":
                #TODO: PARSE
                response_body = manager.delete_tournament()
            else:
                raise ServiceException("Invalid path: '{} {}'".format(resource, method))

        elif resource == "/tournaments/{tournamentId}/brackets":
            if method == "GET":
                response_body = manager.get_brackets()
            elif method == "POST":
                # TODO: Parse request body and pass into create_bracket
                response_body = manager.create_bracket()
            else:
                raise ServiceException("Invalid path: '{} {}'".format(resource, method))

        elif resource == "/tournaments/{tournamentId}/brackets/{bracketId}":
            if method == "GET":
                bracket_id = path_parameters["bracketId"]
                response_body = manager.get_bracket(bracket_id)
            elif method == "PUT":
                # TODO: parse path parameters
                response_body = manager.edit_bracket()
            elif method == "DELETE":
                #TODO: PARSE
                response_body = manager.delete_bracket()
            else:
                raise ServiceException("Invalid path: '{} {}'".format(resource, method))

        elif resource == "/tournaments/{tournamentId}/brackets/{bracketId}/matches":
            if method == "GET":
                #TODO: PARSE
                response_body = manager.get_match()
            else:
                raise ServiceException("Invalid path: '{} {}'".format(resource, method))

        elif resource == "/tournaments/{tournamentId}/brackets/{bracketId}/matches/{matchId}":
            if method == "GET":
                #TODO: PARSE
                response_body = manager.get_match()
            elif method == "PUT":
                #TODO: PARSE
                response_body = manager.edit_match()
            else:
                raise ServiceException("Invalid path: '{} {}'".format(resource, method))

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
