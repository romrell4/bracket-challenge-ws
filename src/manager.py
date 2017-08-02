import da

from service_exception import ServiceException

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
        bracket["rounds"] = self.get_rounds(bracket_id)
        return bracket

    @staticmethod
    def get_rounds(bracket_id):
        matches = da.get_matches(bracket_id)
        rounds = []
        curr_round = 0
        for match in matches:
            round = match["round"]
            if round == curr_round + 1:
                curr_round = round
                rounds.append([])

            # This means that the rounds did not go sequentially (1, 2, 3...). One was missing...
            if round != curr_round:
                raise ServiceException("The matches for this tournament are corrupted. The bracket will need to be reset.")

            # The -1 is because rounds are one indexed and arrays are zero indexed
            rounds[curr_round - 1].append(match)
        return rounds
