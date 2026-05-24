from .jwt_helper import generate_token

# Users Registrator. DB is in memory: TODO: Implement users DB in Postgres and Convert UserRegistrator in a library


class UserRegistrator:
    def __init__(self):
        self.users_db = {}

    def register_user(self, name, email, password):
        if email in self.users_db:
            return False, {"error": "USER_REGISTERED"}

        ## TODO: Change for a logic that support concurrency on user registration

        user_id = len(self.users_db) + 1

        self.users_db[email] = {
            "id": user_id,
            "name": name,
            "email": email,
            "password": password,  # TODO: Use hashing for password store
        }
        return True, {"results": user_id}

    def login_user(self, email, password):
        if email not in self.users_db:
            return False, {"error": "INVALID_EMAIL"}

        if password != self.users_db[email]["password"]:
            return False, {"error": "INVALID_PASSWORD"}

        token = generate_token(str(self.users_db[email]["id"]))

        return True, {
            "id": self.users_db[email]["id"],
            "token": token,
            "name": self.users_db[email]["name"],
        }

    def get_all_users(self):
        answer = {}
        for key in self.users_db:
            value = self.users_db[key]
            answer[value["id"]] = value["name"]

        return answer

    def clean_db(self):
        self.users_db = {}


user_registrator = UserRegistrator()
