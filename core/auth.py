# core/auth.py

class AuthAPI:
    def __init__(self, client):
        self.client = client

    def send_otp(self, phone):
        """Обычный синхронный запрос"""
        return self.client.post("/api/v1/auth/send-otp", json={
            "phone": phone
        })

    def verify_otp(self, code, phone):
        return self.client.post("/api/v1/auth/verify-otp", json={
            "code": code,
            "phone": phone
        })

    def get_me(self):
        # Метод НЕ принимает token, так как он в self.client.headers
        return self.client.get("/api/v1/accounts/me")