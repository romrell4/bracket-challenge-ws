import requests
from service_exception import ServiceException

def validate_user(token):
    try:
        # This call will also validate that the token is still active
        response = requests.get("https://graph.facebook.com/me?fields=email,name&access_token={}".format(token))
        if response.status_code == 200:
            return response.json()
        else:
            print(response.status_code, response.text)
    except ValueError as e:
        print(e)

    # Unless if we returned a valid user_id, throw a 403
    raise ServiceException("Unauthorized. Provided authentication did not validate", 403)
