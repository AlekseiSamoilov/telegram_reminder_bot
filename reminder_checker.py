import asyncio
import logging
from datetime import datetime
from telegram import Bot
from telegram.error import TelegramError

from config import BOT_TOKEN
from database import get_pending_reminders, delete_reminder

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ReminderChecker:
    """Класс для проверки и отправки напоминаний"""

    def __init__(self, bot_token: str):
        """Инициализация чекера напоминаний"""
        logger.info("🔧 Инициализация чекера напоминаний...")
        self.bot = Bot(token=bot_token)
        self.is_running = False
        logger.info("✅ Чекер напоминаний инициализирован")

    async def send_reminder(self, user_id: int, text: str, reminder_id: int):
        """Отправляет напоминание пользователю"""
        try:
            message = f"🔔 **НАПОМИНАНИЕ!**\n\n📝 {text}"

            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )

            # Помечаем напоминание как отправленное
            delete_reminder(reminder_id, user_id)

            logger.info(f"✅ Напоминание {reminder_id} отправлено пользователю {user_id}")

        except TelegramError as e:
            logger.error(f"❌ Ошибка отправки напоминания {reminder_id} пользователю {user_id}: {e}")

            if "bot was blocked by the user" in str(e).lower():
                delete_reminder(reminder_id, user_id)
                logger.info(f"🗑️ Напоминание {reminder_id} удалено - пользователь заблокировал бота")

        except Exception as e:
            logger.error(f"❌ Неожиданная ошибка при отправке напоминания {reminder_id}: {e}")

    async def check_pending_reminders(self):
        """Проверяет базу данных на наличие напоминаний для отправки"""
        try:
            logger.debug("🔍 Проверка напоминаний...")

            # Получаем напоминания для отправки
            pending_reminders = get_pending_reminders()

            if pending_reminders:
                logger.info(f"📨 Найдено {len(pending_reminders)} напоминаний для отправки")

                # Создаем задачи для параллельной отправки
                tasks = []
                for reminder_id, user_id, text, remind_time in pending_reminders:
                    logger.info(f"📤 Отправляем напоминание: {text[:50]}... пользователю {user_id}")
                    task = self.send_reminder(user_id, text, reminder_id)
                    tasks.append(task)

                # Выполняем все задачи параллельно
                await asyncio.gather(*tasks, return_exceptions=True)
            else:
                logger.debug("📭 Нет напоминаний для отправки")

        except Exception as e:
            logger.error(f"❌ Ошибка при проверке напоминаний: {e}")
            import traceback
            logger.error(f"Трейсбек: {traceback.format_exc()}")
            # НЕ re-raise - продолжаем работу даже при ошибке

    async def start_checking(self, interval: int = 60):
        """Запускает бесконечный цикл проверки напоминаний"""
        self.is_running = True
        logger.info(f"🚀 Запуск проверки напоминаний каждые {interval} секунд")
        logger.info(f"✅ Флаг is_running установлен в: {self.is_running}")

        try:
            iteration = 0
            while self.is_running:
                iteration += 1
                logger.debug(f"🔄 Итерация #{iteration}, is_running = {self.is_running}")

                # Проверяем напоминания
                await self.check_pending_reminders()

                # Проверяем флаг перед ожиданием
                if not self.is_running:
                    logger.info("🛑 Получен сигнал остановки")
                    break

                # Ждем указанный интервал, но проверяем is_running каждую секунду
                for i in range(interval):
                    if not self.is_running:
                        logger.info(f"🛑 Получен сигнал остановки во время ожидания")
                        break
                    await asyncio.sleep(1)

                if not self.is_running:
                    break

        except asyncio.CancelledError:
            logger.info("🛑 Задача чекера была отменена")
            self.is_running = False
        except Exception as e:
            logger.error(f"❌ Критическая ошибка в основном цикле проверки: {e}")
            import traceback
            logger.error(f"Трейсбек: {traceback.format_exc()}")
            self.is_running = False
            raise  # Re-raise для диагностики
        finally:
            logger.info("🏁 Чекер напоминаний завершил работу")

    def stop_checking(self):
        """Останавливает проверку напоминаний"""
        logger.info("🛑 Получен запрос на остановку чекера")
        self.is_running = False
        logger.info(f"✅ Флаг is_running установлен в: {self.is_running}")


# Функция для автономного запуска
async def main():
    """Главная функция для запуска чекера как отдельного процесса"""
    checker = ReminderChecker(BOT_TOKEN)

    try:
        # Запускаем проверку каждые 30 секунд
        await checker.start_checking(interval=30)
    except KeyboardInterrupt:
        logger.info("👋 Программа остановлена пользователем")
    finally:
        checker.stop_checking()


if __name__ == '__main__':
    # Запускаем асинхронную функцию
    asyncio.run(main())