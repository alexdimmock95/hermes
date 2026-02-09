"""Callback handlers - COMPLETE FIX for voice message buttons"""

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from src.dictionary.wiktionary_client import (
    format_etymology_for_telegram,
    generate_pronunciation_audio
)
from src.telegram_bot.keyboards import (
    dictionary_result_keyboard,
    build_language_keyboard,
    home_keyboard,
    post_translate_keyboard,
    speed_keyboard
)
from src.telegram_bot.config import LANGUAGES
from src.ml.pronunciation_score import PronunciationScore
from src.learning.events import emit_word_event
from src.learning.aggregations import get_top_words, get_total_words_searched, get_total_searches

# Global scorer instance
PRONUNCIATION_SCORER = None


def get_scorer():
    """Lazy load the pronunciation scorer."""
    global PRONUNCIATION_SCORER
    if PRONUNCIATION_SCORER is None:
        print("Initializing pronunciation scorer for first use...")
        PRONUNCIATION_SCORER = PronunciationScore()
    return PRONUNCIATION_SCORER


async def safe_message_update(query, text, parse_mode="Markdown", reply_markup=None):
    """
    Safely update or send a message, handling both text and non-text messages.
    
    If the original message is a voice/photo/video, send a new text message.
    If it's a text message, edit it.
    """
    try:
        # Try to edit the existing message
        await query.edit_message_text(
            text,
            parse_mode=parse_mode,
            reply_markup=reply_markup
        )
    except Exception as e:
        error_str = str(e).lower()
        if "no text in the message" in error_str or "message can't be edited" in error_str:
            # Original message is voice/photo/video or can't be edited
            # Send a new message instead
            await query.message.reply_text(
                text,
                parse_mode=parse_mode,
                reply_markup=reply_markup
            )
        else:
            # Some other error - re-raise it
            print(f"Error in safe_message_update: {e}")
            raise


async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle all callback query button presses."""
    query = update.callback_query
    await query.answer()
    
    data = query.data
    
    # Language selection
    if data == "choose_language":
        await handle_choose_language(update, context)
    elif data.startswith("lang_"):
        lang_code = data.replace("lang_", "")
        await handle_set_language(update, context, lang_code)
    
    # Dictionary features
    elif data.startswith("pronounce_"):
        word = data.replace("pronounce_", "")
        await handle_pronunciation(update, context, word)
    elif data.startswith("etymology_"):
        word = data.replace("etymology_", "")
        await handle_etymology(update, context, word)
    elif data.startswith("practice_"):
        word = data.replace("practice_", "")
        await handle_practice_mode(update, context, word)
    elif data.startswith("back_def_"):
        word = data.replace("back_def_", "")
        await handle_back_to_definition(update, context, word)
    elif data == "open_dictionary":
        await handle_open_dictionary(update, context)
    elif data == "word_stats":
        await handle_word_stats(update, context)
    
    # Navigation
    elif data == "home":
        await handle_home(update, context)
    elif data == "about":
        await handle_about(update, context)
    elif data == "open_voice_fx":
        await handle_open_voice_fx(update, context)
    elif data.startswith("voice_fx_"):
        await handle_set_voice_fx(update, context, data)
    
    # Speed controls
    elif data == "open_speed":
        await handle_open_speed(update, context)
    elif data.startswith("speed_"):
        speed = data.replace("speed_", "")
        await handle_set_speed(update, context, speed)
    elif data == "close_speed":
        await handle_close_speed(update, context)
    
    else:
        await safe_message_update(query, f"Unknown action: {data}")


# ============================================================================
# LANGUAGE HANDLERS
# ============================================================================

async def handle_choose_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show language selection keyboard."""
    query = update.callback_query
    keyboard = build_language_keyboard(LANGUAGES)
    
    await safe_message_update(
        query,
        "🌍 *Choose your target language:*\n\n"
        "Select the language you want to translate to.",
        reply_markup=keyboard
    )


async def handle_set_language(update: Update, context: ContextTypes.DEFAULT_TYPE, lang_code: str):
    """Set the target language."""
    query = update.callback_query
    
    context.user_data['target_lang'] = lang_code
    lang_name = LANGUAGES.get(lang_code, lang_code)
    
    await safe_message_update(
        query,
        f"✅ *Target language set to: {lang_name}*\n\n"
        f"Send me a voice message and I'll translate it to {lang_name}!",
        reply_markup=home_keyboard()
    )


# ============================================================================
# DICTIONARY HANDLERS
# ============================================================================

async def handle_pronunciation(update: Update, context: ContextTypes.DEFAULT_TYPE, word: str):
    """Send pronunciation audio."""
    query = update.callback_query
    
    try:
        await safe_message_update(
            query,
            f"🔊 Generating pronunciation for *{word}*..."
        )
        
        audio_buffer = generate_pronunciation_audio(word)
        
        await context.bot.send_voice(
            chat_id=query.message.chat_id,
            voice=audio_buffer,
            caption=f"🔊 Pronunciation: *{word}*",
            parse_mode="Markdown"
        )
        
        from src.dictionary.wiktionary_client import format_for_telegram
        definition_text = format_for_telegram(word)
        keyboard = dictionary_result_keyboard(word)
        
        await safe_message_update(query, definition_text, reply_markup=keyboard)
        
    except Exception as e:
        await safe_message_update(
            query,
            f"❌ Sorry, I couldn't generate pronunciation for *{word}*.\n\nError: {str(e)}"
        )


async def handle_etymology(update: Update, context: ContextTypes.DEFAULT_TYPE, word: str):
    """Show etymology information."""
    query = update.callback_query
    
    etymology_text = format_etymology_for_telegram(word)
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back to Definition", callback_data=f"back_def_{word}")]
    ])
    
    await safe_message_update(query, etymology_text, reply_markup=keyboard)


async def handle_practice_mode(update: Update, context: ContextTypes.DEFAULT_TYPE, word: str):
    """Start pronunciation practice mode."""
    query = update.callback_query
    
    context.user_data['practicing_word'] = word
    
    print(f"\n🎤 Practice mode activated for word: '{word}'")
    
    await safe_message_update(
        query,
        f"🎤 *Practice Mode: '{word}'*\n\n"
        f"Record yourself saying '*{word}*' and send me the voice message.\n\n"
        f"I'll analyze your pronunciation using:\n"
        f"• Audio feature analysis (MFCCs)\n"
        f"• Speech recognition (Wav2Vec2)\n"
        f"• Dynamic Time Warping\n\n"
        f"Ready? Press the microphone button 🎤 and say the word!"
    )


async def handle_back_to_definition(update: Update, context: ContextTypes.DEFAULT_TYPE, word: str):
    """Return to definition view."""
    query = update.callback_query
    
    from src.dictionary.wiktionary_client import format_for_telegram
    definition_text = format_for_telegram(word)
    keyboard = dictionary_result_keyboard(word)
    
    await safe_message_update(query, definition_text, reply_markup=keyboard)


async def handle_open_dictionary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt user to enter a word."""
    query = update.callback_query
    
    print("DEBUG: handle_open_dictionary called!")
    context.user_data["awaiting_dictionary_word"] = True
    
    await safe_message_update(
        query,
        "📖 *Dictionary Mode*\n\n"
        "Please type the word you want to look up:"
    )


async def handle_word_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Display word statistics and learning progress."""
    query = update.callback_query
    user_id = update.effective_user.id
    
    try:
        # Get statistics
        total_unique = get_total_words_searched(user_id)
        total_searches = get_total_searches(user_id)
        top_words = get_top_words(user_id, limit=5)
        
        # Build statistics message
        stats_msg = (
            "📊 *Your Learning Statistics*\n\n"
            f"*Total Unique Words:* {total_unique}\n"
            f"*Total Searches:* {total_searches}\n"
        )
        
        if total_unique > 0:
            avg_searches = total_searches / total_unique
            stats_msg += f"*Avg. Searches per Word:* {avg_searches:.1f}\n\n"
        
        if top_words:
            stats_msg += "*🔥 Top 5 Most Searched Words:*\n"
            for i, word_data in enumerate(top_words, 1):
                word = word_data["word"]
                count = word_data["count"]
                # Add emoji based on rank
                emoji = ["🥇", "🥈", "🥉", "4️⃣", "5️⃣"][i - 1]
                stats_msg += f"{emoji} _{word}_ - {count}x\n"
        else:
            stats_msg += "*No words searched yet. Start learning!* 📚"
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="open_dictionary")],
            [InlineKeyboardButton("🏠 Home", callback_data="home")]
        ])
        
        await safe_message_update(query, stats_msg, reply_markup=keyboard)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in word_stats: {error_details}")
        
        error_msg = (
            f"❌ Error loading statistics: {str(e)}\n\n"
            f"This might happen if no words have been searched yet."
        )
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🏠 Home", callback_data="home")]
        ])
        
        await safe_message_update(query, error_msg, reply_markup=keyboard)


# ============================================================================
# NAVIGATION HANDLERS
# ============================================================================

async def handle_home(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Return to main menu."""
    query = update.callback_query
    
    # Clear any active modes
    context.user_data.pop("awaiting_dictionary_word", None)
    context.user_data.pop("practicing_word", None)
    
    current_lang = context.user_data.get('target_lang', 'Not set')
    lang_name = LANGUAGES.get(current_lang, current_lang)
    
    await safe_message_update(
        query,
        f"🏠 *Welcome to the Translation & Dictionary Bot*\n\n"
        f"Current target language: *{lang_name}*\n\n"
        f"What would you like to do?",
        reply_markup=home_keyboard()
    )


async def handle_about(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Show credits and information."""
    query = update.callback_query
    
    about_text = (
        "ℹ️ *About This Bot*\n\n"
        "*Features:*\n"
        "• Voice-to-voice translation\n"
        "• Dictionary with pronunciations\n"
        "• Etymology information\n"
        "• ML-powered pronunciation scoring\n\n"
        "*Credits:*\n"
        "• Translations: Google Translate\n"
        "• Dictionary: Wiktionary\n"
        "• TTS: Coqui XTTS & Google TTS\n"
        "• Speech Recognition: Wav2Vec2 (Meta/Facebook)\n"
        "• Pronunciation Analysis: Custom ML model\n\n"
        "*Technology:*\n"
        "• MFCCs for audio features\n"
        "• Dynamic Time Warping for alignment\n"
        "• Transformer models for speech recognition\n\n"
        "Made with ❤️ for language learners"
    )
    
    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬅️ Back", callback_data="home")]
    ])
    
    await safe_message_update(query, about_text, reply_markup=keyboard)


# ============================================================================
# SPEED HANDLERS
# ============================================================================

async def handle_open_speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open speed adjustment menu."""
    query = update.callback_query
    
    current_speed = context.user_data.get("speed", 1.0)
    
    await safe_message_update(
        query,
        f"🐢 *Adjust Playback Speed*\n\n"
        f"Current speed: *{current_speed}x*\n\n"
        f"Choose a new speed:",
        reply_markup=speed_keyboard()
    )


async def handle_set_speed(update: Update, context: ContextTypes.DEFAULT_TYPE, speed: str):
    """Set playback speed."""
    query = update.callback_query
    
    try:
        speed_float = float(speed)
        context.user_data["speed"] = speed_float
        
        await safe_message_update(
            query,
            f"✅ *Speed set to {speed_float}x*\n\n"
            f"The next audio playback will use this speed.",
            reply_markup=home_keyboard()
        )
    except ValueError:
        await safe_message_update(
            query,
            f"❌ Invalid speed: {speed}",
            reply_markup=home_keyboard()
        )


async def handle_close_speed(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Close speed menu."""
    await handle_home(update, context)

# ============================================================================
# VOICE FX HANDLERS
# ============================================================================

async def handle_open_voice_fx(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Open voice effects menu."""
    query = update.callback_query

    # Set mode
    context.user_data["mode"] = "voice_fx"
    context.user_data.pop("voice_fx_preset", None)

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("⬆️ Male → Female", callback_data="voice_fx_mtf")],
        [InlineKeyboardButton("⬇️ Female → Male", callback_data="voice_fx_ftm")],
        [InlineKeyboardButton("👴 Older", callback_data="voice_fx_older")],
        [InlineKeyboardButton("🧒 Younger", callback_data="voice_fx_younger")],
        [InlineKeyboardButton("⬅️ Back", callback_data="home")]
    ])

    await safe_message_update(
        query,
        "🎛 *Voice Effects*\n\n"
        "Choose how you'd like your voice transformed.\n\n"
        "After selecting an effect, send me a voice message 🎤",
        reply_markup=keyboard
    )

    context.user_data.pop("practicing_word", None)
    context.user_data.pop("awaiting_dictionary_word", None)

async def handle_set_voice_fx(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    data: str
):
    """Set selected voice FX preset."""
    query = update.callback_query

    preset_map = {
        "voice_fx_mtf": "male_to_female",
        "voice_fx_ftm": "female_to_male",
        "voice_fx_older": "older",
        "voice_fx_younger": "younger",
    }

    preset = preset_map.get(data)

    if preset is None:
        await safe_message_update(query, "❌ Unknown voice effect.")
        return

    context.user_data["mode"] = "voice_fx"
    context.user_data["voice_fx_preset"] = preset

    await safe_message_update(
        query,
        f"✅ *Voice effect set: {preset.replace('_', ' ').title()}*\n\n"
        "Now send me a voice message and I’ll transform it 🎤✨",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("⬅️ Back", callback_data="open_voice_fx")],
            [InlineKeyboardButton("🏠 Home", callback_data="home")]
        ])
    )