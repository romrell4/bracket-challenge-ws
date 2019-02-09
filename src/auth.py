import requests
from service_exception import ServiceException

def validate_user(event):
    try:
        # Lower case all the keys, then look for token
        token = {k.lower(): v for k, v in event["headers"].items()}["token"]

        # This call will also validate that the token is still active
        response = requests.get("https://graph.facebook.com/me?fields=email,name&access_token={}".format(token))
        if response.status_code == 200:
            fb_user = response.json()
            if "email" not in fb_user:
                raise ServiceException("Unable to retrieve email from auth token. Please log out and back in.")
            return fb_user
        else:
            print(response.status_code, response.text)
    except (KeyError, ValueError) as e:
        print(e)

    # Unless if we returned a valid user_id, throw a 403
    raise ServiceException("Unauthorized. Provided authentication did not validate", 403)
