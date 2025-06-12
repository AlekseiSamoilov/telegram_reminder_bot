import asyncio
import signal
import logging
from typing import List
from telegram.ext import Application

from config import BOT_TOKEN
from main import setup_handlers
from reminder_checker import ReminderChecker
from database import init_database

# МАКСИМАЛЬНЫЙ уровень логирования для поиска проблемы
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.DEBUG  # 🔍 Включаем DEBUG уровень
)
logger = logging.getLogger(__name__)


class DebugBotManager:

    def __init__(self):
        self.app = None
        self.reminder_checker = None
        self.tasks: List[asyncio.Task] = []
        self.is_stopping = False

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

    async def debug_telegram_bot(self):
        """Отладочная обертка для Telegram бота"""
        try:
            logger.info("🚀 ЗАПУСК: Telegram polling...")
            await self.app.updater.start_polling(drop_pending_updates=True)
            logger.info("✅ ЗАВЕРШЕНИЕ: Telegram polling завершен нормально")
        except Exception as e:
            logger.error(f"❌ ОШИБКА в Telegram боте: {e}")
            import traceback
            logger.error(f"Трейсбек: {traceback.format_exc()}")
            raise

    async def debug_reminder_checker(self):
        """Отладочная обертка для чекера напоминаний"""
        try:
            logger.info("🚀 ЗАПУСК: Чекер напоминаний...")
            await self.reminder_checker.start_checking(interval=30)
            logger.info("✅ ЗАВЕРШЕНИЕ: Чекер напоминаний завершен нормально")
        except Exception as e:
            logger.error(f"❌ ОШИБКА в чекере напоминаний: {e}")
            import traceback
            logger.error(f"Трейсбек: {traceback.format_exc()}")
            raise

    async def start_services_debug(self):
        logger.info("🚀 Запуск всех сервисов (DEBUG режим)...")

        tasks = []

        # Запуск Telegram бота с отладкой
        if self.app:
            logger.info("📱 Создание задачи для Telegram бота...")
            bot_task = asyncio.create_task(
                self.debug_telegram_bot(),
                name="telegram_bot_debug"
            )
            tasks.append(bot_task)
            logger.info("📱 Задача Telegram бота создана")

        # Запуск чекера напоминаний с отладкой
        if self.reminder_checker:
            logger.info("⏰ Создание задачи для чекера напоминаний...")
            checker_task = asyncio.create_task(
                self.debug_reminder_checker(),
                name="reminder_checker_debug"
            )
            tasks.append(checker_task)
            logger.info("⏰ Задача чекера напоминаний создана")

        self.tasks = tasks
        logger.info(f"📋 Всего задач создано: {len(tasks)}")

        # Ждем 2 секунды чтобы задачи запустились
        logger.info("⏳ Ожидание 2 секунды для стабилизации...")
        await asyncio.sleep(2)

        # Проверяем состояние задач
        for i, task in enumerate(tasks):
            task_name = task.get_name()
            if task.done():
                logger.error(f"❌ Задача '{task_name}' уже завершена!")
                if task.exception():
                    logger.error(f"❌ Исключение в '{task_name}': {task.exception()}")
                else:
                    logger.warning(f"⚠️ Задача '{task_name}' завершена без исключения")
            else:
                logger.info(f"✅ Задача '{task_name}' работает")

        try:
            logger.info("🔄 Запуск основного цикла ожидания...")

            # Вместо gather используем wait с timeout для лучшей диагностики
            done, pending = await asyncio.wait(
                tasks,
                timeout=10,  # Ждем максимум 10 секунд
                return_when=asyncio.FIRST_COMPLETED  # Останавливаемся при первом завершении
            )

            logger.info(f"📊 Завершено задач: {len(done)}, Ожидает: {len(pending)}")

            # Анализируем завершенные задачи
            for task in done:
                task_name = task.get_name()
                if task.exception():
                    logger.error(f"❌ Задача '{task_name}' завершена с ошибкой: {task.exception()}")
                else:
                    logger.warning(f"⚠️ Задача '{task_name}' завершена без ошибки")

            # Если есть незавершенные задачи, отменяем их
            for task in pending:
                logger.info(f"🛑 Отмена задачи '{task.get_name()}'")
                task.cancel()

        except Exception as e:
            logger.error(f"❌ Критическая ошибка в основном цикле: {e}")
            import traceback
            logger.error(f"Трейсбек: {traceback.format_exc()}")
            raise

    async def stop_services(self):
        if self.is_stopping:
            logger.info("⚠️ Остановка уже в процессе...")
            return

        self.is_stopping = True
        logger.info("🛑 Остановка сервисов...")

        if self.reminder_checker:
            self.reminder_checker.stop_checking()
            logger.info("⏰ Чекер напоминаний остановлен")

        # Отменяем все задачи
        for task in self.tasks:
            if not task.done():
                task.cancel()

        # Останавливаем Telegram бота
        if self.app:
            try:
                if hasattr(self.app, 'updater') and self.app.updater and self.app.updater.running:
                    await self.app.updater.stop()
                    logger.info("📱 Updater остановлен")

                await self.app.stop()
                await self.app.shutdown()
                logger.info("🤖 Telegram бот остановлен")

            except Exception as e:
                logger.error(f"Ошибка при остановке Telegram бота: {e}")

        logger.info("✅ Все сервисы остановлены")


async def main():
    bot_manager = None

    try:
        logger.info("🎯 ДИАГНОСТИЧЕСКИЙ запуск бота...")

        bot_manager = DebugBotManager()

        await bot_manager.setup_bot()
        await bot_manager.setup_reminder_checker()

        logger.info("🎉 Все компоненты инициализированы!")
        logger.info("🔍 Запуск в режиме диагностики...")

        await bot_manager.start_services_debug()

    except KeyboardInterrupt:
        logger.info("👋 Программа остановлена пользователем")
    except Exception as e:
        logger.error(f"❌ Критическая ошибка: {e}")
        import traceback
        logger.error(f"Полный трейсбек: {traceback.format_exc()}")
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