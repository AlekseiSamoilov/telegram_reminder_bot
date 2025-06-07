import logging
from wsgiref.util import application_uri

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import BOT_TOKEN

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text('Привет! Я бот для напоминаний 🔔')

def main():

    app = Application.builder().token(BOT_TOKEN).job_queue(None).build()
    app.add_handler(CommandHandler("start", start))

    print("Бот запущен...")
    app.run_polling(drop_pending_updates=True)

if __name__ == '__main__':
    main()
