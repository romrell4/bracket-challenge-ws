import json

from manager import Manager
import auth
from service_exception import ServiceException

def lambda_handler(event, context):
    try:
        if event is None or "resource" not in event or "httpMethod" not in event:
            raise ServiceException("Invalid request. No 'resource', or 'httpMethod' found in event", 400)

        resource, method = event["resource"], event["httpMethod"] # These will be used to specify which endpoint was being hit
        path_parameters = event["pathParameters"] # This will be used to get IDs and other parameters from the URL
        try:
            body = json.loads(event["body"]) # This will be used for most POSTs and PUTs
        except:
            body = None

        fb_user = auth.validate_user(event)

        manager = Manager(fb_user["email"])

        if resource == "/users":
            if method == "POST":
                response_body = manager.login(fb_user)
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
