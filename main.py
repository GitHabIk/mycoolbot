import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackContext
import requests
import os

from datetime import datetime
import asyncio
from typing import Dict

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего Telegram-бота
TOKEN = "TOKEN"

if not TOKEN:
    raise ValueError("Токен не найден! Проверьте Secrets в Replit")

# UniverseId, который мы проверяем
TARGET_UNIVERSE_ID = 7090482051

# Хранилище для задач автообновления
user_tasks: Dict[int, asyncio.Task] = {}
user_messages: Dict[int, int] = {}

async def get_roblox_stats():
    """Получает статистику из Roblox API."""
    try:
        url = f"https://games.roblox.com/v1/games?universeIds={TARGET_UNIVERSE_ID}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()

        if not data["data"]:
            return None

        game_data = data["data"][0]
        return {
            "name": game_data.get("name", "N/A"),
            "playing": game_data.get("playing", "N/A"),
            "visits": game_data.get("visits", "N/A"),
            "favorits": game_data.get("favoritedCount", "N/A"),
            "time": datetime.now().strftime("%H:%M:%S")
        }
    except Exception as e:
        logger.error(f"Ошибка при запросе к Roblox API: {e}")
        return None

async def update_stats(context: CallbackContext, chat_id: int, message_id: int):
    """Обновляет статистику в сообщении."""
    while True:
        try:
            stats = await get_roblox_stats()
            if stats:
                text = (
                    f"📊 Автообновляемая статистика {stats['name']}\n"
                    f"🕒 Последнее обновление: {stats['time']}\n"
                    f"👥 Игроков онлайн: {stats['playing']}\n"
                    f"🚪 Всего посещений: {stats['visits']}\n"
                    f"⭐ Всего фаворитов: {stats['favorits']}\n"
                    f"\nЧтобы остановить: /stopauto"
                )
                await context.bot.edit_message_text(
                    chat_id=chat_id,
                    message_id=message_id,
                    text=text
                )
            await asyncio.sleep(60)  # Обновление каждую минуту
        except Exception as e:
            logger.error(f"Ошибка автообновления: {e}")
            break

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение."""
    await update.message.reply_text(
        "Привет! Я бот для проверки статистики в Острове Блоптоп.\n"
        "Используй команды:\n"
        "/online - разовая проверка\n"
        "/autoonline - автообновление (каждую минуту)\n"
        "/stopauto - остановить автообновление"
    )

async def online(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Разовая проверка статистики."""
    stats = await get_roblox_stats()
    if stats:
        await update.message.reply_text(
            f"📊 Статистика {stats['name']}\n"
            f"👥 Игроков онлайн: {stats['playing']}\n"
            f"🚪 Всего посещений: {stats['visits']}\n"
            f"⭐ Всего фаворитов: {stats['favorits']}"
        )
    else:
        await update.message.reply_text("❌ Не удалось получить данные")

async def autoonline(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Включает автообновление статистики."""
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id
    
    # Если уже есть активное автообновление - останавливаем
    if user_id in user_tasks:
        user_tasks[user_id].cancel()
        del user_tasks[user_id]
    
    # Отправляем начальное сообщение
    stats = await get_roblox_stats()
    if not stats:
        await update.message.reply_text("❌ Не удалось получить данные")
        return
    
    msg = await update.message.reply_text(
        f"📊 Автообновляемая статистика {stats['name']}\n"
        f"🕒 Последнее обновление: {stats['time']}\n"
        f"👥 Игроков онлайн: {stats['playing']}\n"
        f"🚪 Всего посещений: {stats['visits']}\n"
        f"⭐ Всего фаворитов: {stats['favorits']}\n"
        f"\nЧтобы остановить: /stopauto"
    )
    
    # Сохраняем ID сообщения
    user_messages[user_id] = msg.message_id
    
    # Запускаем задачу автообновления
    task = asyncio.create_task(update_stats(context, chat_id, msg.message_id))
    user_tasks[user_id] = task
    
    logger.info(f"Автообновление включено для {user_id}")

async def stopauto(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Останавливает автообновление."""
    user_id = update.effective_user.id
    
    if user_id in user_tasks:
        user_tasks[user_id].cancel()
        del user_tasks[user_id]
        await update.message.reply_text("✅ Автообновление остановлено")
        logger.info(f"Автообновление выключено для {user_id}")
    else:
        await update.message.reply_text("ℹ️ У вас нет активного автообновления")

def main() -> None:
    """Запуск бота."""
    # Запуск веб-сервера
    logger.info("Веб-сервер запущен. Сообщение 'I'm alive' доступно на сайте")

    # Инициализация бота
    application = Application.builder().token(TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("online", online))
    application.add_handler(CommandHandler("autoonline", autoonline))
    application.add_handler(CommandHandler("stopauto", stopauto))

    logger.info("Бот запускается...")
    application.run_polling()

if __name__ == "__main__":
    main()
