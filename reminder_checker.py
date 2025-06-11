import asyncio
import logging

from datetime import date
from pyexpat.errors import messages

from telegram import Bot
from telegram.error import TelegramError

from config import BOT_TOKEN
from database import get_pending_reminders, delete_reminder

# Настройка логирования
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Класс для проверки и отправки напоминаний
class ReminderChecker:

    # Инициализация чекера напоминаний
    # токен бота как аргумент
    def __init__(self, bot_token: str):

        self.bot = Bot(token=bot_token)
        self.is_running = False

    # Отправляет пользователю напоминание
    # user_id: ID пользователя в Телеграмме (целое число)
    # text: Текст напоминания (строка)
    # reminder_id: ID напоминания (целое число)
    async def send_reminder(self, user_id: int, text: str, reminder_id: int):
        try:
            message = f"🔔 **НАПОМИНАНИЕ!**\n\n📝 {text}"

            await self.bot.send_message(
                chat_id=user_id,
                text=message,
                parse_mode='Markdown'
            )

            delete_reminder(reminder_id, user_id)

            logger.info(f"напоминание {reminder_id} отправлено пользователю {user_id}")

        except TelegramError as e:
            logger.error(f"Ошибка при отправке напоминания {reminder_id} пользователю {user_id}: {e}")

            if "bot blocked by the user" in str(e).lower():
                delete_reminder(reminder_id, user_id)
                logger.info(f"Напоминание {reminder_id} удалено - пользователь заблокировал бота")

        except Exception as e:
            logger.error(f"Неожиданная ошибка при отправке напоминания {reminder_id}: {e}")

    async def check_pending_reminders(self):
        try:
            # Получаем все напоминания, время которых наступило
            pending_reminders = get_pending_reminders()

            if pending_reminders:
                logger.info(f"Найдено {len(pending_reminders)} напоминаний для отправки")

                # Создаем список задачи для параллельной отправки
                tasks = []
                for reminder_id, user_id, text, remind_time in pending_reminders:

                    task = self.send_reminder(user_id, text, reminder_id)
                    tasks.append(task)
                # Выполняем все задачи параллельно
                await asyncio.gather(*tasks, return_exceptions=True)

        except Exception as e:
            logger.error(f"Ошибка при проверке напоминаний: {e}")

    async def start_checking(self, interval: int = 60):

        while self.is_running:
            try:
                # Проверяем напоминания
                await self.check_pending_reminders()

                # Ждем указанный интервал перед следующей проверкой
                await asyncio.sleep(interval)

            except KeyboardInterrupt:

                logger.info("Получен сигнал остановки")
                self.stop_checking()

            except Exception as e:

                logger.error(f"Ошибка в основном цикле проверки {e}")
                await asyncio.sleep(interval)

    def stop_checking(self):
        self.is_running = False
        logger.info("Проверка напоминаний остановлена")

async def main():
    checker = ReminderChecker(BOT_TOKEN)

    try:
        # Запускаем проверку каждые 30 секунд
        await checker.start_checking(interval=30)
    except KeyboardInterrupt:
        logger.info("Программа остановлена пользователем")
    finally:
        checker.stop_checking()

if __name__ == '__main__':
    asyncio.run(main())





