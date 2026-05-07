import os

import pytest
import httpx
from dotenv import load_dotenv
from core.users import UsersAPI
from core.user import UserAPI
from utils.tg_report import send_telegram_report

load_dotenv()


@pytest.fixture(scope="session")
def guest_client():
    """Постоянный гостевой клиент без авторизации"""
    with httpx.Client(base_url=os.getenv("BASE_URL"), timeout=10.0) as client:
        yield client

@pytest.fixture(scope="session")
def auth_client():
    """Постоянный авторизованный клиент"""
    base_url = os.getenv("BASE_URL")
    with httpx.Client(base_url=base_url, timeout=10.0) as client:
        # Прямой запрос на логин без сторонних классов
        login_response = client.post("/web/v2/users/login_with_password/", json={
            "username": "+998998987882",
            "password": "Sh2004Sh"
        })

        if login_response.status_code == 200:
            token = login_response.json().get("token")
            # Навешиваем токен на все будущие запросы этого клиента
            client.headers.update({"Authorization": f"Token {token}"})
        else:
            pytest.exit(f"Setup failed: Could not login. Status: {login_response.status_code}")

        yield client


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Хук, который вызывается после завершения всех тестов"""

    # Собираем статистику
    stats = {
        "total": terminalreporter._numcollected,
        "passed": len(terminalreporter.stats.get('passed', [])),
        "failed": len(terminalreporter.stats.get('failed', [])),
        "errors": len(terminalreporter.stats.get('error', [])),
    }

    # Отправляем отчет
    send_telegram_report(os.getenv("TG_TOKEN"), os.getenv("TG_CHAT_ID"), stats)