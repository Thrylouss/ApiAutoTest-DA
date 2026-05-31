import os
import time

import pytest
import httpx
from dotenv import load_dotenv
from utils.tg_report import send_telegram_report

load_dotenv()

# Глобальное время старта прогона
_run_start_ts = None


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
        phone = "998000000000"
        code = "1234"  # Убедись, что это правильный код для тестового стенда

        # 1. Запрос на получение OTP
        send_otp_response = client.post("/api/v1/auth/send-otp", json={"phone": phone})

        if send_otp_response.status_code == 200:
            # 2. Передаем данные в verify-otp (ОБЯЗАТЕЛЬНО!)
            verify_otp_response = client.post("/api/v1/auth/verify-otp", json={
                "phone": phone,
                "code": code
            })

            if verify_otp_response.status_code == 200:
                token = verify_otp_response.json()["accessToken"]
            else:
                # Выводим тело ответа, чтобы понять причину 400
                pytest.exit(
                    f"Setup failed: Could not login. Status: {verify_otp_response.status_code}, Response: {verify_otp_response.text}")

            # 3. Важный момент: посмотри, какой тип авторизации ждет сервер.
            # Если в документации написано "Bearer", то "Token" может не сработать.
            client.headers.update({"Authorization": f"Bearer {token}"})

        else:
            pytest.exit(
                f"Setup failed: Could not login. Status: {send_otp_response.status_code}, Response: {send_otp_response.text}")

        yield client


def pytest_sessionstart(session):
    global _run_start_ts
    _run_start_ts = time.time()


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Отправка отчёта в TG после завершения прогона."""

    # Если переменная BOT_RUN_ID есть — значит запуск инициирован ботом,
    # тогда токен/chat_id может быть переопределён через env.
    token = os.getenv("TG_TOKEN")
    chat_id = os.getenv("TG_CHAT_ID")

    if not token or not chat_id:
        return  # Не настроено — молча выходим

    stats = {
        "total": terminalreporter._numcollected,
        "passed": len(terminalreporter.stats.get("passed", [])),
        "failed": len(terminalreporter.stats.get("failed", [])),
        "errors": len(terminalreporter.stats.get("error", [])),
    }

    failures = terminalreporter.stats.get("failed", [])
    errors = terminalreporter.stats.get("error", [])

    # Маркер из ENV — его пробрасывает бот при запуске по команде
    marker = os.getenv("RUN_MARKER")

    duration = None
    if _run_start_ts:
        duration = time.time() - _run_start_ts

    send_telegram_report(
        token=token,
        chat_id=chat_id,
        stats=stats,
        failures=failures,
        errors=errors,
        marker=marker,
        duration=duration,
    )