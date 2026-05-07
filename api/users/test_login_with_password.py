import pytest
from core.users import UsersAPI


class TestAuth:

    def test_login_success(self, auth_client):
        auth_api= UsersAPI(auth_client)
        response = auth_api.login("+998998987882", "Sh2004Sh")
        assert response.status_code == 200
        data = response.json()
        # Проверяем наличие токена (исправлено на 'token', как в твоих логах)
        assert "token" in data

    @pytest.mark.parametrize("username, password, expected_status", [
        ("+998998987882", "wrong_password", 400),
        ("", "", 400),
        ("+998000000000", "any_pass", 400),
    ])
    def test_login_negative(self, auth_client, username, password, expected_status):
        auth_api = UsersAPI(auth_client)
        response = auth_api.login(username, password)
        # Если тест упадет, ты увидишь AssertionError, а не RuntimeError
        assert response.status_code == expected_status

    def test_login_response_structure(self, auth_client):
        auth_api = UsersAPI(auth_client)
        response = auth_api.login("+998998987882", "Sh2004Sh")
        data = response.json()
        assert isinstance(data.get("token"), str)