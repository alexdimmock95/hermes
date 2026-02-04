"""Callback query handlers for the Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes
import soundfile as sf

from src.telegram_bot.config import LANGUAGES
from src.telegram_bot.keyboards import (
    build_language_keyboard,
    post_translate_keyboard,
    speed_keyboard,
    home_keyboard, dictionary_result_keyboard
)
from src.telegram_bot.utils import change_speed
from src.dictionary.wiktionary_client import format_etymology_for_telegram, generate_pronunciation_audio, format_for_telegram


async def handle_choose_language(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle the 'choose_language' callback."""
    reply_markup = build_language_keyboard(LANGUAGES, buttons_per_row=2)
    # Can't edit a voice message's text — send a new message instead
    await query.message.reply_text(
        text="🌍 Choose your target language:",
        reply_markup=reply_markup
    )


async def handle_language_selection(query, context: ContextTypes.DEFAULT_TYPE, lang_code: str):
    """Handle when a specific language is selected."""
    context.user_data["target_lang"] = lang_code

    if query.message.text:
        # Came from the language picker (text message) — collapse it in place
        await query.edit_message_text(text=f"Translating to {LANGUAGES[lang_code]}.\nSend a voice note or text.")
    else:
        # Came from the voice message caption ("Reply in" button) — can't edit that,
        # so just send the prompt as a new message
        await query.message.reply_text(f"Translating to {LANGUAGES[lang_code]}.\nSend a voice note or text.")


async def handle_open_speed(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle opening the speed adjustment menu."""
    await query.edit_message_reply_markup(reply_markup=speed_keyboard())


async def handle_close_speed(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle closing the speed adjustment menu (back button)."""
    translate_into = context.user_data.get("last_detected_lang", "en")

    await query.edit_message_reply_markup(
        reply_markup=post_translate_keyboard(
            last_detected_lang=translate_into
        )
    )


async def handle_speed_change(query, context: ContextTypes.DEFAULT_TYPE, factor: float):
    """Handle actual speed change."""
    prev_audio_path = context.user_data.get("last_audio_translated")
    sr = 16000

    if prev_audio_path is None:
        await query.message.reply_text("⚠️ No translated audio available to modify.")
        return

    modified_audio = change_speed(prev_audio_path, factor, sr)

    output_path = "speed_changed.wav"
    sf.write(output_path, modified_audio, sr)
    await query.message.reply_voice(open(output_path, "rb"))


async def handle_home(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle returning to the home menu."""
    await query.message.reply_text(
        text="🏡 Home",
        reply_markup=home_keyboard()
    )

'''
async def handle_open_dictionary(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle opening the dictionary feature."""
    # Can't edit a voice message's text — send a new message instead
    await query.message.reply_text("📖 Send me a word to define (text or voice).")
    context.user_data["awaiting_dictionary_word"] = True
'''

async def handle_open_dictionary(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle opening the dictionary feature."""
    print("DEBUG: handle_open_dictionary called!")
    print(f"DEBUG: Setting awaiting_dictionary_word to True")
    context.user_data["awaiting_dictionary_word"] = True
    print(f"DEBUG: awaiting_dictionary_word is now: {context.user_data.get('awaiting_dictionary_word')}")
    
    # Can't edit a voice message's text — send a new message instead
    await query.message.reply_text("📖 Send me a word to define (text or voice).")


async def handle_etymology(query, context: ContextTypes.DEFAULT_TYPE, word: str):
    """Handle etymology lookup for a word."""
    from telegram import InlineKeyboardButton, InlineKeyboardMarkup
    
    etymology_text = format_etymology_for_telegram(word)
    
    # Send etymology as a new message
    await query.message.reply_text(
        etymology_text,
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔍 Look up another word", callback_data="open_dictionary")],
            [InlineKeyboardButton("🏠 Home", callback_data="home")]
        ])
    )


async def handle_about(query, context: ContextTypes.DEFAULT_TYPE):
    """Handle the about page."""
    about_text = (
        "🤖 *hermes*\n\n"
        "A multilingual speech-to-speech translation bot powered by state-of-the-art AI models.\n\n"
        "🌍 Choose your target language and send a voice note or text to translate.\n"
        "🎧 Receive translated audio with options to adjust speed and more.\n\n"
        "Developed by Alex Dimmock.\n"
        "https://github.com/alexdimmock95/hermes/tree/main"
    )

    await query.message.reply_text(about_text, parse_mode="Markdown")


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Main callback query router that delegates to specific handlers."""
    query = update.callback_query
    await query.answer()

    if query.data == "choose_language":
        await handle_choose_language(query, context)

    elif query.data.startswith("lang_"):
        lang_code = query.data.replace("lang_", "")
        await handle_language_selection(query, context, lang_code)

    elif query.data == "open_speed":
        await handle_open_speed(query, context)

    elif query.data == "close_speed":
        await handle_close_speed(query, context)

    elif query.data.startswith("speed_"):
        factor = float(query.data.split("_")[1])
        await handle_speed_change(query, context, factor)

    elif query.data == "home":
        await handle_home(query, context)

    elif query.data == "open_dictionary":
        await handle_open_dictionary(query, context)

    elif query.data.startswith("etymology_"):
        word = query.data.replace("etymology_", "")
        await handle_etymology(query, context, word)

    elif query.data == "about":
        await handle_about(query, context)

    elif query.data.startswith("pronounce_"):
        word = query.data.replace("pronounce_", "")
        await handle_pronunciation(query, context, word)

async def handle_pronunciation(query, context: ContextTypes.DEFAULT_TYPE, word: str):
    """Handle pronunciation button - send audio file."""
    
    try:
        # Show processing message
        await query.edit_message_text(f"🔊 Generating pronunciation for *{word}*...")
        
        # Generate audio
        audio_buffer = generate_pronunciation_audio(word)
        
        # Send audio file
        await context.bot.send_voice(
            chat_id=query.message.chat_id,
            voice=audio_buffer,
            caption=f"🔊 Pronunciation: *{word}*"
        )
        
        # Restore original message
        definition_text = format_for_telegram(word)
        keyboard = dictionary_result_keyboard(word)
        await query.edit_message_text(definition_text, reply_markup=keyboard)
        
    except Exception as e:
        await query.edit_message_text(f"❌ Couldn't generate pronunciation: {str(e)}")