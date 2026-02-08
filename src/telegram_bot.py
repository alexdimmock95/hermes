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
from src.telegram_bot.callbacks import handle_buttons
from src.ml.pronunciation_score import PronunciationScore


def main():
    app = Application.builder().token(TOKEN).build()

    # Pre-load ML model at startup
    print("Loading ML models...")
    from src.telegram_bot.callbacks import get_scorer
    scorer = get_scorer()  # This caches it
    print("✓ ML models ready")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("translate", set_language))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()

if __name__ == '__main__':
    main()


### TODO: Add in the voice distortion, male female options in forst set of buttons, "voice effects"
###### TODO: Add in capability to press "pronunciation" or "syntax" for IPA, tongue position/shape info and word type, grammar info, respectively.
### TODO/ language aware wiktionary - if detected language is french, wiktionary french version
### TODO: What other models other than xtts can I use? Ones that are ideally faster, more languages
## TODO: make sure definition given back is all POS, so that it doesnt cut halfway through the second POS
### TODO: Difficulty classifier - Train a model to rate word difficulty (A1-C2 levels);
### TODO:Word embeddings - Create/use embeddings to find similar words; maybe with each word look up, show synonyms on a scale from A1-C2, via embeddings?
# ### TODO:Finalise the definition database process
 ## TODO: is there a way to do proper formant shifting to change accent using DTW modification? 
## TODO: dictionary mode > look up word (english) > translate to target language > show definition in target language, with option to show english definition as well. Dictionary in multiple languages not picking words even in their correct spelling and language. 

## python -m src.telegram_bot ##