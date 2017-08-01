import da

class Manager:
    def __init__(self, username):
        self.user = da.get_user_by_username(username)

    def login(self, fb_user):
        # Check if they are registering or logging in
        if self.user is None:
            # They are registering a new account
            new_user = {
                "username": fb_user["email"],
                "name": fb_user["name"]
            }
            return da.create_user(new_user)
        else:
            # They are logging in. Return the user attached to their authentication token
            return self.user

    def get_tournaments(self):
        return da.get_tournaments()

    def get_bracket(self, bracket_id):
        bracket = da.get_bracket(bracket_id)
        bracket["matches"] = da.get_matches(bracket_id)
        return bracket
