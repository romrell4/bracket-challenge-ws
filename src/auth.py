from service_exception import ServiceException
from res import properties

import requests

def validate(event):
    try:
        token = event["headers"]["Authorization"]
        response = requests.get("https://graph.facebook.com/debug_token?input_token={}&access_token={}".format(token, properties.app_access_token)).json()
        data = response["data"]
        if data["app_id"] == properties.app_id and data["is_valid"] and data["user_id"] is not None:
            return data["user_id"]
    except (KeyError, ValueError) as e:
        print(e)

    # Unless if we returned a valid user_id, throw a 403
    raise ServiceException("Unauthorized. Provided authentication did not validate", 403)
