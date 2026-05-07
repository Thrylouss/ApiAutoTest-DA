import pytest
from core.auth import AuthAPI


class TestAuth:

    def test_login_success(self, guest_client):
        auth_api= AuthAPI(guest_client)
        send_otp_response = auth_api.send_otp("998000000000")
        assert send_otp_response.status_code == 200
        verify_otp_response = auth_api.verify_otp("0000","998000000000")
        data = verify_otp_response.json()
        # Проверяем наличие токена (исправлено на 'token', как в твоих логах)
        assert "accessToken" in data

    def test_login_negative(self, guest_client):
        auth_api = AuthAPI(guest_client)
        send_otp_response = auth_api.send_otp("998000000000")
        assert send_otp_response.status_code == 200
        verify_otp_response = auth_api.verify_otp("1111", "998000000000")
        # Проверяем наличие токена (исправлено на 'token', как в твоих логах)
        assert verify_otp_response.status_code == 400

    def test_login_empty_phone(self, guest_client):
        auth_api = AuthAPI(guest_client)
        send_otp_response = auth_api.send_otp("")
        assert send_otp_response.status_code == 400


