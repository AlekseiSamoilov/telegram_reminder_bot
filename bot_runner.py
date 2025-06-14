import asyncio
import logging
from telegram.ext import Application

from config import BOT_TOKEN
from main import setup_handlers
from database import init_database
from reminder_checker import ReminderChecker, logger

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def run_bot():
    logging.info("Запускаем бота")

    init_database()

    app = Application.builder().token(BOT_TOKEN).job_queue(None).build()

    setup_handlers(app)

    logger.info("Телеграмм бот готов к работе!")
    await app.run_polling(drop_pending_updates=True)

