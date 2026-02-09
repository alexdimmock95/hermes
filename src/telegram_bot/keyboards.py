"""Keyboard builders for the Telegram bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.telegram_bot.config import LANGUAGES


def post_translate_keyboard(last_detected_lang):
    """Keyboard shown after translation with options to reply, change language, adjust speed, or go home."""
    lang_label = LANGUAGES.get(last_detected_lang, last_detected_lang)
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton(
                f"🔁 Translate to {lang_label}",
                callback_data=f"lang_{last_detected_lang}"
            )
        ],
        [
            InlineKeyboardButton("🌍 Choose another language", callback_data="choose_language")
        ],
        [
            InlineKeyboardButton("🐢 Speed", callback_data="open_speed")
        ],
        [
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]
    ])


def dictionary_result_keyboard(word: str) -> InlineKeyboardMarkup:
    """
    Keyboard shown after displaying dictionary definition.
    
    Includes:
    - Pronunciation audio playback
    - Etymology information
    - Practice pronunciation with ML scoring
    - Word statistics
    - Look up another word
    - Return home
    """
    keyboard = [
        [
            InlineKeyboardButton("🔊 Pronunciation", callback_data=f"pronounce_{word}"),
            InlineKeyboardButton("📜 Etymology", callback_data=f"etymology_{word}")
        ],
        [
            InlineKeyboardButton("🎤 Practice Pronunciation", callback_data=f"practice_{word}")
        ],
        [
            InlineKeyboardButton("🔍 Look up another word", callback_data="open_dictionary")
        ],
        [
            InlineKeyboardButton("📊 My Stats", callback_data="word_stats")
        ],
        [
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]
    ]
    
    return InlineKeyboardMarkup(keyboard)

def speed_keyboard():
    """Speed adjustment submenu (0.5x / 1x / 2x) with a back arrow."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🐌 0.5x", callback_data="speed_0.5"),
         InlineKeyboardButton("1x",      callback_data="speed_1.0"),
         InlineKeyboardButton("🐇 2x",   callback_data="speed_2.0")],
        [InlineKeyboardButton("← Back",  callback_data="close_speed")]
    ])


def home_keyboard():
    """Main menu keyboard shown at the start and when returning home."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Choose target language", callback_data="choose_language")],
        [InlineKeyboardButton("📖 Dictionary", callback_data="open_dictionary")],
        [InlineKeyboardButton("🎛 Voice Effects", callback_data="open_voice_fx")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ])


def build_language_keyboard(lang_map, buttons_per_row=3):
    """Build a keyboard with language selection buttons."""
    keyboard = []
    row = []

    for code, label in lang_map.items():
        row.append(
            InlineKeyboardButton(label, callback_data=f"lang_{code}")
        )
        if len(row) == buttons_per_row:
            keyboard.append(row)
            row = []

    if row:
        keyboard.append(row)

    return InlineKeyboardMarkup(keyboard)