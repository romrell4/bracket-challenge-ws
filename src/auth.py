import requests
from service_exception import ServiceException
import firebase_admin
from firebase_admin import auth

firebase_admin.initialize_app()

def validate_user(event):
    # Lower case all the keys, then look for token
    headers = {k.lower(): v for k, v in event["headers"].items()}
    facebook_token = headers.get("token")
    firebase_token = headers.get("x-firebase-token")

    if facebook_token is not None:
        # This call will also validate that the token is still active
        response = requests.get("https://graph.facebook.com/me?fields=email,name&access_token={}".format(facebook_token))
        if response.status_code == 200:
            fb_user = response.json()
            if "email" not in fb_user:
                raise ServiceException("Unable to retrieve email from authentication token. Please log out and back in.", 401)
            return fb_user
        else:
            print(response.status_code, response.text)
            raise ServiceException("Unable to authenticate with Facebook. Please log out and back in.", 401)
    elif firebase_token is not None:
        try:
            return auth.verify_id_token(firebase_token)
        except Exception as e:
            print(e)
            raise ServiceException("Unable to authenticate with Firebase. Please log out and back in.", 401)
    else:
        raise ServiceException("Unable to find token in request", 401)
