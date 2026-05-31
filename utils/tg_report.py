# utils/tg_report.py
import requests
from datetime import datetime

TG_API = "https://api.telegram.org"
MAX_MESSAGE_LEN = 4000  # Telegram limit ~4096, оставляем запас


def _escape_md(text: str) -> str:
    """Экранирование для Markdown (классический, не V2)."""
    if not text:
        return ""
    for ch in ("_", "*", "`", "["):
        text = text.replace(ch, f"\\{ch}")
    return text


def _send_message(token: str, chat_id: str, text: str, parse_mode: str = "Markdown"):
    """Низкоуровневая отправка одного сообщения."""
    url = f"{TG_API}/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": text,
        "parse_mode": parse_mode,
        "disable_web_page_preview": True,
    }
    try:
        return requests.post(url, json=payload, timeout=10)
    except Exception as e:
        print(f"Ошибка отправки в TG: {e}")
        return None


def _split_long(text: str, limit: int = MAX_MESSAGE_LEN):
    """Разбивает длинный текст на части по limit символов, по переносам строк."""
    if len(text) <= limit:
        return [text]

    parts, buf = [], ""
    for line in text.splitlines(keepends=True):
        if len(buf) + len(line) > limit:
            parts.append(buf)
            buf = line
        else:
            buf += line
    if buf:
        parts.append(buf)
    return parts


def _format_failure(item) -> str:
    """
    Из pytest TestReport достаём имя теста и краткое сообщение об ошибке.
    item — это объект из terminalreporter.stats['failed' | 'error']
    """
    nodeid = getattr(item, "nodeid", "unknown")
    # longreprtext доступен у TestReport; fallback на str(longrepr)
    repr_text = getattr(item, "longreprtext", None) or str(getattr(item, "longrepr", ""))

    # Берём только последнюю значимую строку (обычно там assert / exception)
    last_line = ""
    for line in reversed(repr_text.splitlines()):
        line = line.strip()
        if line and not line.startswith(("_", "=", "-")):
            last_line = line
            break

    # Подрезаем длинные сообщения
    if len(last_line) > 250:
        last_line = last_line[:250] + "..."

    return f"• `{_escape_md(nodeid)}`\n   ↳ {_escape_md(last_line)}"


def send_telegram_report(token, chat_id, stats, failures=None, errors=None, marker=None, duration=None):
    """
    Отправляет отчёт в Telegram.

    :param stats: dict с ключами total, passed, failed, errors
    :param failures: список TestReport провалившихся тестов (опц.)
    :param errors: список TestReport ошибок (опц.)
    :param marker: если запуск был по маркеру — указать (для контекста)
    :param duration: длительность прогона в секундах
    """
    failures = failures or []
    errors = errors or []

    is_green = stats["failed"] == 0 and stats["errors"] == 0
    status_icon = "✅" if is_green else "❌"

    header = (
        f"{status_icon} *Автотесты завершены*\n\n"
        f"📊 *Результаты:*\n"
        f"🔹 Всего: {stats['total']}\n"
        f"✅ Пройдено: {stats['passed']}\n"
        f"❌ Провалено: {stats['failed']}\n"
        f"⚠️ Ошибки: {stats['errors']}\n"
    )

    if duration is not None:
        header += f"⏱ Длительность: {duration:.1f}s\n"
    if marker:
        header += f"🏷 Маркер: `{_escape_md(marker)}`\n"

    header += f"🕒 Среда: `DA`\n📅 {datetime.now().strftime('%Y-%m-%d %H:%M')}"

    _send_message(token, chat_id, header)

    # Детали провалов и ошибок — отдельными сообщениями
    if failures:
        body = "❌ *Failed tests:*\n\n" + "\n\n".join(_format_failure(f) for f in failures)
        for part in _split_long(body):
            _send_message(token, chat_id, part)

    if errors:
        body = "⚠️ *Errors:*\n\n" + "\n\n".join(_format_failure(e) for e in errors)
        for part in _split_long(body):
            _send_message(token, chat_id, part)