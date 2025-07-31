import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import requests

# Настройка логгирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Токен вашего Telegram-бота
TOKEN = "7665428689:AAEBSUzgQDtwSkCNszJcGt4a6ilad5kDcRE"

# UniverseId, который мы проверяем
TARGET_UNIVERSE_ID = 7090482051

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Отправляет приветственное сообщение при команде /start."""
    await update.message.reply_text(
        "Привет! Я бот для проверки онлайна в Roblox.\n"
        f"Используй команду /online, чтобы узнать статистику по UniverseId {TARGET_UNIVERSE_ID}."
    )

async def get_online(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    print("BABA")
    """Получает онлайн и посещения по заданному UniverseId."""
    try:
        url = f"https://games.roblox.com/v1/games?universeIds={TARGET_UNIVERSE_ID}"
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        
        if not data["data"]:
            await update.message.reply_text("❌ UniverseId не найден")
            return
        
        game_data = data["data"][0]
        name = game_data.get("name", "N/A")
        playing = game_data.get("playing", "N/A")
        visits = game_data.get("visits", "N/A")
        favorits = game_data.get("favoritedCount", "N/A")
        
        await update.message.reply_text(
            f"📊 Статистика {name}\n"
            f"👥 Игроков онлайн: {playing}\n"
            f"🚪 Всего посещений: {visits}\n"
            f"⭐ Всего фаворитов: {favorits}"
        )
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        await update.message.reply_text("❌ Произошла ошибка при запросе к Roblox API")

def main() -> None:
    """Запуск бота."""
    application = Application.builder().token(TOKEN).build()

    # Регистрация команд
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("online", get_online))

    # Запуск бота
    application.run_polling()

if __name__ == "__main__":
    main()