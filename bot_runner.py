import asyncio
import signal
import logging
from typing import List
from telegram.ext import Application

from config import BOT_TOKEN
from main import setup_handlers
from reminder_checker import ReminderChecker
from database import init_database

logging.basicConfig(
    format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

class BotManager:

    def __init__(self):
        self.app = None
        self.reminder_checker = None
        self.tasks: List[asyncio.Task] = []

    async def setup_bot(self):
        logger.info("🤖 Инициализация Telegram бота...")

        init_database()

        self.app = Application.builder().token(BOT_TOKEN).job_queue(None).build()

        setup_handlers(self.app)

        await self.app.initialize()
        await self.app.start()

        logger.info("✅ Telegram бот инициализирован")

    async def setup_reminder_checker(self):

        logger.info("⏰ Инициализация чекера напоминаний...")

        self.reminder_checker = ReminderChecker(BOT_TOKEN)

        logger.info("✅ Чекер напоминаний инициализирован")

    async def start_service(self):
        logger.info("🚀 Запуск всех сервисов...")

        # Создаем задачи для параллельного выполнения
        tasks = []

        # Запуск Телеграм бота
        if self.app:
            bot_task = asyncio.create_task(
                self.app.updater.start_polling(drop_pending_updates = True),
                name = "telegram_bot"
            )
            tasks.append(bot_task)
            logger.info("Телеграм бот запущен")

        # Запуск чекера напоминаний
        if self.reminder_checker:
            checker_task = asyncio.create_task(
                self.reminder_checker.start_checking(interval=30),
                name='reminder_checker'
            )
            tasks.append(checker_task)
            logger.info("Чекер напоминаний запущен")

        self.tasks = tasks

        try:
            await asyncio.gather(*tasks)
        except Exception as e:
            logger.error(f"Ошибка в однои из сервисов: {e}")
            raise

    async def stop_services(self):
        logger.info("Остановка сервисов")

        if self.reminder_checker:
            await self.reminder_checker.start_checking()
            logger.info("Чекер напоминаний остановлен")

        # Отменяем все асинхронные задачи
        for task in self.tasks:
            if not task.done():
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass #Это нормально при отмене

        if self.app:
            await self.app.stop()
            await self.app.shutdown()
            logger.info("Телеграм бот остановлен")

        logger.info("Все сервисы остановлены")

bot_manager = None

def signal_handler(signum, frame):

    logger.info(f"Получен сигнал {signum}. Завершение работы...")

    if bot_manager:

        loop = asyncio.get_event_loop()
        if loop.is_running():

            asyncio.create_task(bot_manager.stop_services())
        else:
            loop.run_until_complete(bot_manager.stop_services())

async def main():
    global bot_manager

    try:
        logger.info("🎯 Запуск бота для напоминаний...")

        bot_manager = BotManager()

        signal.signal(signal.SIGINT, signal_handler)
        signal.signal(signal.SIGTERM, signal_handler)

        await bot_manager.setup_bot()
        await bot_manager.setup_reminder_checker()

        logger.info("🎉 Все компоненты инициализированы! Бот готов к работе!")
        logger.info("📝 Доступные команды: /start, /help, /remind, /list, /delete")
        logger.info("💡 Для остановки нажмите Ctrl+C")

        await bot_manager.start_service()

    except KeyboardInterrupt:
        logger.info("👋 Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        raise
    finally:
        if bot_manager:
            await bot_manager.stop_services()

if __name__ == '__main__':

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 До свидания!")
    except Exception as e:
        print(f"❌ Ошибка запуска: {e}")
