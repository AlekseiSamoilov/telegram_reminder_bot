import logging
from datetime import datetime
from email.utils import parsedate_to_datetime
from mimetypes import inited
from wsgiref.util import application_uri

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN
from database import init_database, add_reminder, get_active_reminders, delete_reminder
from time_parser import parse_time, format_time

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        '🔔Привет! Я бот для напоминаний!\n\n'
        'Доступные команды:\n'
        '❓ /help - показать справку\n'
        '📝 /remind - создать напоминание\n'
        '📋 /list - показать активные напоминания\n\n'
        'Примеры:\n'
        '• /remind через 30 минут Проверить почту\n'
        '• /remind завтра в 15:00 Встреча с клиентом'
    )

async def help_command(update:Update, context: ContextTypes.DEFAULT_TYPE):
    help_text = '''
    🔔 **Бот для напоминаний - Справка**
    
    **Команды:**
    📝 `/remind <время> <текст>` - создать напоминание
    📋 `/list` - показать все активные напоминания  
    🗑 `/delete <номер>` - удалить напоминание по номеру
    ❓ `/help` - эта справка
    
    **Форматы времени:**
    ⏰ `через 30 минут` - относительное время
    ⏰ `через 2 часа` - относительное время
    ⏰ `сегодня в 18:00` - время сегодня
    ⏰ `завтра в 09:30` - время завтра  
    ⏰ `15:45` - время сегодня (если не прошло) или завтра
    ⏰ `2024-06-10 14:30` - точная дата и время
    
    **Примеры:**
    - `/remind через 15 минут Позвонить маме`
    - `/remind завтра в 08:00 Утренняя пробежка`
    - `/remind сегодня в 20:00 Посмотреть фильм`
    - `/remind 2024-06-15 10:00 День рождения друга`
    '''

    await update.message.reply_text(help_text, parse_mode='Markdown')

async def remind_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args: #Если нет аргументов после команды
        await update.message.reply_text(
            '❌ Укажите время и текст напоминания!\n\n'
            'Пример: `/remind через 30 минут Проверить почту`',
            parse_mode='Markdown'
        )
        return
    #Объединяем все слова обратно в строку
    full_text = ' '.join(context.args)

    words = full_text.split()
    reminder_time = None
    reminder_text = ''

    for i in range(2, min(7, len(words) + 1)):
        time_part = ' '.join(words[:i])
        text_part = ' '.join(words[i:])

        parsed_time = parse_time(time_part)

        if parsed_time and text_part:
            reminder_time = parsed_time
            reminder_text = text_part
            break

    if not reminder_time or not reminder_text:
        await update.message.reply_text(
            '❌ Не удалось распознать время или текст напоминания!\n\n'
            'Проверьте формат:\n'
            '• `/remind через 30 минут текст напоминания`\n'
            '• `/remind завтра в 15:00 текст напоминания`',
            parse_mode='Markdown'
        )
        return
    # получаем id пользователя из Телеграмма
    user_id = update.effective_user.id

    try:
        # сохраняем напоминание в БД
        reminder_id = add_reminder(user_id, reminder_text, reminder_time)
        # форматируем время для показа пользователю
        formatted_time = format_time(reminder_time)

        await update.message.reply_text(
            f'✅ Напоминание создано!\n\n'
            f'📝 **Текст:** {reminder_text}\n'
            f'⏰ **Время:** {formatted_time}\n'
            f'🆔 **ID:** {reminder_id}',
            parse_mode='Markdown'
        )

    except Exception as e: #Если произошла ошибка при сохранении
        logging.error(f"Ошибка при создании напоминания: {e}")
        await update.message.reply_text(
            '❌ Произошла ошибка при создании напоминания. Попробуйте еще раз.'
        )

async def list_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    try:
        reminders = get_active_reminders(user_id)

        if not reminders:
            await update.message.reply_text(
                '📭 У вас нет активных напоминаний.\n\n'
                'Создайте новое: `/remind через 30 минут текст`',
                parse_mode='Markdown'
            )
            return

        message_list = ['📋 **Ваши активные напоминания:**\n']

        for i, (reminder_id, text, reminder_time_str, created_at) in enumerate(reminders, 1):
#             Конвертируем строку времени обратно в datetime
#             formatted_time = format_time(remind_time)
            remind_time = datetime.fromisoformat(reminder_time_str)
            formatted_time = format_time(remind_time)

            # Добавляем строку с информацией о напоминании
            message_list.append(
                f'{i}. 📝 {text}\n'
                f'   ⏰ {formatted_time}\n'
                f'   🆔 ID: {reminder_id}\n'
            )

            message = '\n'.join(message_list)

            message += '\n\n💡 Для удаления: `/delete <ID>`'

            await update.message.reply_text(message, parse_mode='Markdown')

    except Exception as e:
        logging.error(f"Ошибка при получении списка напоминаний: {e}")
        await update.message.reply_text(
            '❌ Произошла ошибка при получении списка напоминаний.'
        )

async def delete_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if not context.args:
        await update.message.reply_text(
            '❌ Укажите ID напоминания для удаления!\n\n'
            'Пример: `/delete 5`\n'
            'Посмотреть ID: `/list`',
            parse_mode='Markdown'
        )
        return
    try:
        reminder_id = int(context.args[0])
    except ValueError:
        await update.message.reply_text(
            '❌ ID должен быть числом!\n\n'
            'Пример: `/delete 5`',
            parse_mode='Markdown'
        )
        return

    user_id = update.effective_user.id

    try:
        success = delete_reminder(reminder_id, user_id)

        if success:
            await update.message.reply_text(
                f'✅ Напоминание #{reminder_id} удалено!'
            )
        else:
            await update.message.reply_text(
                f'❌ Напоминание #{reminder_id} не найдено или не принадлежит вам.'
            )
    except Exception as e:
        logging.error(f"Ошибка при удалении напоминания:{e}")
        await update.message.reply_text(
            '❌ Произошла ошибка при удалении напоминания.'
        )

def setup_handlers(app: Application):

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("remind", remind_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("delete", delete_command))

def main():

    init_database()

    app = Application.builder().token(BOT_TOKEN).job_queue(None).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(CommandHandler("remind", remind_command))
    app.add_handler(CommandHandler("list", list_command))
    app.add_handler(CommandHandler("delete", delete_command))

    print("🤖 Бот запущен и готов к работе!")
    print("📝 Доступные команды: /start, /help, /remind, /list, /delete")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
