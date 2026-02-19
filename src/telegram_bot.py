from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Load .env file
load_dotenv(Path(__file__).parent.parent / '.env')

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if TOKEN is None:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

from src.telegram_bot.config import LANGUAGES
from src.telegram_bot.utils import change_speed
from src.telegram_bot.handlers import start, set_language, handle_voice, handle_message
from src.telegram_bot.callbacks import handle_buttons, get_classifier
from src.ml.pronunciation_score import PronunciationScore
from src.learning.storage import initialise_db


def main():
    app = Application.builder().token(TOKEN).build()

    # Initialize learning database
    print("Initializing learning database...")
    initialise_db()
    print("✓ Database ready")

    # ML models load on first use (lazy loading) to keep startup fast
    # They'll be cached after first use, so second+ requests are instant
    print("✓ ML models ready (loading on demand)")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("translate", set_language))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()

#TODO: see word form extractor for english conjugations. being parsed weirdly. 