import asyncio
import os
import sys
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from aiogram.types import Message
from dotenv import load_dotenv

load_dotenv()

# Настройки (лучше вынести в .env)
TOKEN = os.getenv("TG_TOKEN")
# ID группы, куда бот присылает отчеты (чтобы ограничить доступ к запуску)
ALLOWED_CHAT_ID = os.getenv("TG_CHAT_ID")

bot = Bot(token=TOKEN)
dp = Dispatcher()

@dp.message(Command("start_test"))
async def handle_start_test(message: Message):
    # Проверка безопасности (запускать может только админ или участник конкретной группы)
    # if message.chat.id != ALLOWED_CHAT_ID:
    #     return await message.answer("❌ Запуск тестов разрешен только из рабочей группы.")

    await message.answer("🚀 <b>Запуск автотестов DA API...</b>\nРезультаты придут в группу после завершения.", parse_mode="HTML")

    # Формируем команду. Если у вас используются маркеры, можно добавить -m
    # Например: "pytest --alluredir=reports"
    pytest_command = [sys.executable, "-m", "pytest", "-v"]

    # Запускаем pytest асинхронно
    process = await asyncio.create_subprocess_exec(
        *pytest_command,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        cwd=os.getcwd() # Запуск из текущей директории проекта
    )

    # Ждем завершения
    stdout, stderr = await process.communicate()

    if process.returncode == 0:
        await message.reply("✅ Тесты завершены успешно (PASSED).")
    elif process.returncode == 1:
        await message.reply("⚠️ Тесты завершены. Есть упавшие кейсы (FAILED). Проверьте основной отчет.")
    else:
        error_info = stderr.decode()
        await message.reply(f"❌ Ошибка при выполнении pytest:\n<pre>{error_info[:500]}</pre>", parse_mode="HTML")

async def main():
    print("Бот-раннер для DA запущен и ждет команду /start_test")
    await dp.start_polling(bot)

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass