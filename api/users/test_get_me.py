import pytest
from core.auth import AuthAPI


class TestAuthUser:

    def test_get_me_success(self, auth_client):
        # auth_client уже содержит токен (см. conftest.py)
        auth_api = AuthAPI(auth_client)
        response = auth_api.get_me()

        assert response.status_code == 200
        assert response.json()["success"] is True

    def test_get_me_unauthorized(self, guest_client):
        # guest_client НЕ содержит токена
        auth_api = AuthAPI(guest_client)
        response = auth_api.get_me()
        assert response.status_code == 401