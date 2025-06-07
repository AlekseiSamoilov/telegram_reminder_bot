import logging
from wsgiref.util import application_uri

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот для напоминаний 🔔\n\n'
        'Доступные команды:\n'
        '/help - показать справку\n'
        '/remind - создать напоминание\n'
        '/list - показать активные напоминания'
    )

async def help_command(update:Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        'Команды для бота:\n\n'
        '/start - приветствие\n'
        '/help - эта справка\n'
        '/remind <время> <текст> - создать напоминание\n'
        '/list - показать все напоминания\n\n'
        'Примеры:\n'
        '/remind через 30 минут проверить почту\n'
        '/remind завтра в 15:00 Встреча с клиентом\n'
    )

def main():

    app = Application.builder().token(BOT_TOKEN).job_queue(None).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))

    print("Бот запущен...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
