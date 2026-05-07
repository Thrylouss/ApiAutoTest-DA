

class UsersAPI:
    def __init__(self, client):
        self.client = client

    def login(self, username, password):
        """Обычный синхронный запрос"""
        return self.client.post("/web/v2/users/login_with_password/", json={
            "username": username,
            "password": password
        })