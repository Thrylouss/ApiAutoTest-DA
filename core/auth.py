

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