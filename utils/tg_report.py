import requests


def send_telegram_report(token, chat_id, stats):
    """Отправляет отчет в Telegram группу"""

    # Формируем текст отчета с эмодзи
    status_icon = "✅" if stats['failed'] == 0 and stats['errors'] == 0 else "❌"

    message = (
        f"{status_icon} *Автотесты завершены*\n\n"
        f"📊 *Результаты:*\n"
        f"🔹 Всего: {stats['total']}\n"
        f"✅ Пройдено: {stats['passed']}\n"
        f"❌ Провалено: {stats['failed']}\n"
        f"⚠️ Ошибки: {stats['errors']}\n\n"
        f"🕒 Среда: `Mobilux`"
    )

    url = f"https://api.telegram.org/bot{token}/sendMessage"
    payload = {
        "chat_id": chat_id,
        "text": message,
        "parse_mode": "Markdown"
    }

    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Ошибка отправки в TG: {e}")