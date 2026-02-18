"""Keyboard builders for the Telegram bot."""

from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from src.telegram_bot.config import LANGUAGES, LANGUAGES_BY_FAMILY, DIFFICULTY_SUPPORTED_LANGUAGES

def home_keyboard():
    """Main menu keyboard shown at the start and when returning home."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🌍 Choose target language", callback_data="choose_language")],
        [InlineKeyboardButton("📖 Dictionary", callback_data="open_dictionary")],
        [InlineKeyboardButton("🎛 Voice Effects", callback_data="open_voice_fx")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")]
    ])

def build_language_keyboard(buttons_per_row=2):
    """
    Build a keyboard with all languages.
    Buttons are arranged 2 per row across all families (no singles in middle).
    """
    keyboard = []
    row = []
    
    for family_name, languages in LANGUAGES_BY_FAMILY.items():
        # Add languages from this family
        for code, label in languages.items():
            row.append(
                InlineKeyboardButton(label, callback_data=f"lang_{code}")
            )
            if len(row) == buttons_per_row:
                keyboard.append(row)
                row = []
    
    # Append any remaining buttons at the very end
    if row:
        keyboard.append(row)
    
    keyboard.append([InlineKeyboardButton("🏠 Home", callback_data="home")])

    return InlineKeyboardMarkup(keyboard)

def post_translate_keyboard(last_detected_lang, translated_word=None, target_lang=None):
    """
    Keyboard shown after translation with options to reply in another language.
    
    Args:
        last_detected_lang: Language code for next translation target (e.g., 'en', 'fr')
        translated_word: Optional translated word to add dictionary button if single word
        target_lang: Optional target language code for dictionary lookup
    """
    lang_label = LANGUAGES.get(last_detected_lang, last_detected_lang)
    # Extract just the language name without the extra text for clarity
    # e.g., "🇬🇧 English" or "🇷🇺 Русский (Russkij)" -> keep as is but cleaner
    lang_name_only = lang_label.split("(")[0].strip()  # Remove parenthetical content if any
    
    keyboard = []
    
    # Add dictionary button if translated_word is a single word
    if translated_word and target_lang:
        # Check if it's a single word (no spaces, allow hyphens/apostrophes for compound words)
        cleaned_word = translated_word.strip()
        # Remove common punctuation but keep hyphens and apostrophes
        word_only = ''.join(c for c in cleaned_word if c.isalnum() or c in "-'")
        # Check if it's a single word (no spaces, reasonable length)
        # Telegram callback_data limit is 64 bytes, so keep it short
        if word_only and ' ' not in cleaned_word and len(word_only) <= 40:
            # Use | as separator (unlikely to appear in words)
            callback_data = f"dict_lookup_{word_only.lower()}|{target_lang}"
            if len(callback_data) <= 64:  # Telegram limit
                keyboard.append([
                    InlineKeyboardButton(
                        "📖 Dictionary",
                        callback_data=callback_data
                    )
                ])
    
    keyboard.extend([
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
    
    return InlineKeyboardMarkup(keyboard)

def speed_keyboard():
    """Speed adjustment submenu (0.5x / 1x / 2x) with a back arrow."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🐌 0.5x", callback_data="speed_0.5"),
         InlineKeyboardButton("🚶‍♂️1x",      callback_data="speed_1.0"),
         InlineKeyboardButton("🐇 2x",   callback_data="speed_2.0")],
        [InlineKeyboardButton("🏠 Home",  callback_data="home")]
    ])

def dictionary_result_keyboard(word: str, language_code: str = None) -> InlineKeyboardMarkup:
    """
    Keyboard shown after displaying dictionary definition.
    
    Includes:
    - Pronunciation audio playback
    - Etymology information
    - Practice pronunciation with ML scoring
    - Word statistics
    - Look up another word
    - Return home
    
    Smart Synonyms (difficilty) button only shows for supported languages.
    """
    keyboard = [
        [
            InlineKeyboardButton("🔊 Pronunciation", callback_data=f"pronounce_{word}"),
            InlineKeyboardButton("📜 Etymology", callback_data=f"etymology_{word}")
        ],
    ]
    
    # Only show Smart Synonyms if language is supported for CEFR difficulty
    if language_code and language_code in DIFFICULTY_SUPPORTED_LANGUAGES:
        keyboard.append([
            InlineKeyboardButton("🧠 Smart Synonyms", callback_data=f"smart_synonyms_{word}")
        ])
    
    keyboard.extend([
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
    ])
    
    return InlineKeyboardMarkup(keyboard)

def difficulty_result_keyboard(word: str) -> InlineKeyboardMarkup:
    """
    Keyboard shown on the difficulty & synonyms screen.
    Lets the user go back to the full definition or look up another word.
    """
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("⬅️ Back to Definition", callback_data=f"back_def_{word}")
        ],
        [
            InlineKeyboardButton("🔍 Look up another word", callback_data="open_dictionary")
        ],
        [
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]
    ])