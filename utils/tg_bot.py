# utils/tg_bot.py
"""
Telegram-бот для запуска автотестов по командам.

Запуск:
    python -m utils.tg_bot

Команды:
    /help               — список команд
    /run                — запустить все тесты
    /run <marker>       — запустить тесты по маркеру (smoke, regression, product, user, ...)
    /markers            — показать доступные маркеры
    /status             — статус последнего/текущего запуска

Защита: бот принимает команды только из ALLOWED_CHAT_IDS (через запятую в .env).
"""
import os
import re
import sys
import time
import subprocess
import threading
from pathlib import Path

import requests
from dotenv import load_dotenv

load_dotenv()

TG_API = "https://api.telegram.org"
TOKEN = os.getenv("TG_TOKEN")
DEFAULT_CHAT_ID = os.getenv("TG_CHAT_ID")
ALLOWED_CHAT_IDS = {
    s.strip() for s in os.getenv("ALLOWED_CHAT_IDS", DEFAULT_CHAT_ID or "").split(",") if s.strip()
}
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Список разрешённых маркеров — настраивается под проект.
# Можно подтягивать из pytest.ini автоматически, но безопаснее white-list.
KNOWN_MARKERS = {
    "smoke": "Быстрая проверка ключевых эндпоинтов",
    "regression": "Полный регрессионный прогон",
    "product": "Тесты модуля product",
    "user": "Тесты модуля user",
    "users": "Тесты модуля users",
    "auth": "Тесты авторизации",
}

# Регэксп для имени маркера — защищает от инъекций в shell
MARKER_RE = re.compile(r"^[a-zA-Z_][a-zA-Z0-9_]*$")

# Состояние
_state = {
    "running": False,
    "started_at": None,
    "marker": None,
    "last_finished_at": None,
    "last_marker": None,
    "last_exit_code": None,
}
_state_lock = threading.Lock()


# ---------- Telegram helpers ----------

def send(chat_id, text, parse_mode="Markdown"):
    try:
        requests.post(
            f"{TG_API}/bot{TOKEN}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
            timeout=10,
        )
    except Exception as e:
        print(f"[send] error: {e}")


def get_updates(offset=None, timeout=30):
    """Long-polling запрос обновлений."""
    params = {"timeout": timeout}
    if offset is not None:
        params["offset"] = offset
    try:
        r = requests.get(
            f"{TG_API}/bot{TOKEN}/getUpdates",
            params=params,
            timeout=timeout + 5,
        )
        return r.json().get("result", [])
    except Exception as e:
        print(f"[get_updates] error: {e}")
        time.sleep(3)
        return []


# ---------- Команды ----------

def cmd_help(chat_id, _args):
    text = (
        "*🤖 Бот автотестов DA*\n\n"
        "*Команды:*\n"
        "`/run` — запустить все тесты\n"
        "`/run <marker>` — запустить по маркеру\n"
        "`/markers` — список маркеров\n"
        "`/status` — статус прогона\n"
        "`/help` — эта справка"
    )
    send(chat_id, text)


def cmd_markers(chat_id, _args):
    lines = ["*🏷 Доступные маркеры:*\n"]
    for m, desc in KNOWN_MARKERS.items():
        lines.append(f"• `{m}` — {desc}")
    lines.append("\nПример: `/run smoke`")
    send(chat_id, "\n".join(lines))


def cmd_status(chat_id, _args):
    with _state_lock:
        if _state["running"]:
            elapsed = time.time() - _state["started_at"]
            marker = _state["marker"] or "all"
            send(chat_id, f"⏳ *Идёт прогон* `{marker}`\nУже: {elapsed:.0f}s")
        elif _state["last_finished_at"]:
            ago = time.time() - _state["last_finished_at"]
            send(
                chat_id,
                f"💤 Не выполняется.\n"
                f"Последний прогон: `{_state['last_marker'] or 'all'}` "
                f"({ago:.0f}s назад, exit={_state['last_exit_code']})",
            )
        else:
            send(chat_id, "💤 Тесты ещё не запускались.")


def cmd_run(chat_id, args):
    marker = args[0] if args else None

    if marker:
        if not MARKER_RE.match(marker):
            send(chat_id, f"❌ Некорректное имя маркера: `{marker}`")
            return
        if marker not in KNOWN_MARKERS:
            send(
                chat_id,
                f"❌ Неизвестный маркер `{marker}`.\n"
                f"Посмотри `/markers`.",
            )
            return

    with _state_lock:
        if _state["running"]:
            send(chat_id, "⚠️ Прогон уже выполняется. Дождись завершения или /status.")
            return
        _state["running"] = True
        _state["started_at"] = time.time()
        _state["marker"] = marker

    label = f"`{marker}`" if marker else "*all*"
    send(chat_id, f"🚀 Запускаю тесты: {label}")

    thread = threading.Thread(
        target=_run_pytest,
        args=(chat_id, marker),
        daemon=True,
    )
    thread.start()


def _run_pytest(chat_id, marker):
    """Запуск pytest в отдельном процессе. Отчёт уйдёт через pytest_terminal_summary."""
    cmd = [sys.executable, "-m", "pytest", "-v"]
    if marker:
        cmd += ["-m", marker]

    env = os.environ.copy()
    # Гарантируем, что conftest отправит отчёт в правильный чат
    env["TG_CHAT_ID"] = str(chat_id)
    env["RUN_MARKER"] = marker or ""

    try:
        result = subprocess.run(
            cmd,
            cwd=PROJECT_ROOT,
            env=env,
            capture_output=True,
            text=True,
            timeout=60 * 30,  # 30 минут максимум
        )
        exit_code = result.returncode
    except subprocess.TimeoutExpired:
        send(chat_id, "⏰ Прогон превысил таймаут (30 мин) и был прерван.")
        exit_code = -1
    except Exception as e:
        send(chat_id, f"💥 Ошибка запуска pytest: `{e}`")
        exit_code = -2

    with _state_lock:
        _state["running"] = False
        _state["last_finished_at"] = time.time()
        _state["last_marker"] = marker
        _state["last_exit_code"] = exit_code
        _state["started_at"] = None
        _state["marker"] = None


# ---------- Роутер ----------

COMMANDS = {
    "/help": cmd_help,
    "/start": cmd_help,
    "/run": cmd_run,
    "/markers": cmd_markers,
    "/status": cmd_status,
}


def handle_update(update):
    msg = update.get("message") or update.get("edited_message")
    if not msg:
        return

    chat_id = str(msg["chat"]["id"])
    text = (msg.get("text") or "").strip()

    if not text.startswith("/"):
        return

    # Допуск только из разрешённых чатов
    if ALLOWED_CHAT_IDS and chat_id not in ALLOWED_CHAT_IDS:
        send(chat_id, "🚫 Этот чат не авторизован для управления тестами.")
        print(f"[security] Rejected chat_id={chat_id}")
        return

    parts = text.split()
    # Поддержка /run@botname args
    cmd = parts[0].split("@")[0].lower()
    args = parts[1:]

    handler = COMMANDS.get(cmd)
    if handler:
        handler(chat_id, args)
    else:
        send(chat_id, f"❓ Неизвестная команда `{cmd}`. См. /help")


# ---------- Main loop ----------

def main():
    if not TOKEN:
        print("ERROR: TG_TOKEN не задан в .env")
        sys.exit(1)

    print(f"Bot started. Allowed chats: {ALLOWED_CHAT_IDS or '(any)'}")
    print(f"Project root: {PROJECT_ROOT}")

    offset = None
    while True:
        updates = get_updates(offset=offset, timeout=30)
        for update in updates:
            offset = update["update_id"] + 1
            try:
                handle_update(update)
            except Exception as e:
                print(f"[handle_update] error: {e}")


if __name__ == "__main__":
    main()