from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, CallbackQueryHandler
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
import tempfile
import soundfile as sf
import os
import sys
import librosa
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Load .env file
load_dotenv(Path(__file__).parent.parent / '.env')

TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
if TOKEN is None:
    raise RuntimeError("TELEGRAM_BOT_TOKEN is not set")

from src.speech_to_speech import SpeechToSpeechTranslator
from src.voice_transformer import VoiceTransformer
from src.dictionary.wiktionary_client import format_for_telegram, format_etymology_for_telegram
from src.latiniser import latinise
from src.latiniser import NON_LATIN_LANGS

LANGUAGES = {
    "en": "🇬🇧 English (English)",
    "es": "🇪🇸 Español (Spanish)",
    "fr": "🇫🇷 Français (French)",
    "de": "🇩🇪 Deutsch (German)",
    "it": "🇮🇹 Italiano (Italian)",
    "pt": "🇵🇹 Português (Portuguese)",
    "pl": "🇵🇱 Polski (Polish)",
    "tr": "🇹🇷 Türkçe (Turkish)",
    "ru": "🇷🇺 Русский (Russian)",
    "nl": "🇳🇱 Nederlands (Dutch)",
    "cs": "🇨🇿 Čeština (Czech)",
    "ar": "🇸🇦 العربية (Arabic)",
    "zh-CN": "🇨🇳 简体中文 (Chinese Simplified)",
    "zh-TW": "🇨🇳 中文 (Chinese)",
    "ja": "🇯🇵 日本語 (Japanese)",
    "hu": "🇭🇺 Magyar (Hungarian)",
    "ko": "🇰🇷 한국어 (Korean)",
    "hi": "🇮🇳 हिन्दी (Hindi)"
}

# Initialize translator
translator = SpeechToSpeechTranslator(device="cpu", model_size="base")

def post_translate_keyboard(last_detected_lang):
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

def dictionary_result_keyboard(word):
    """Keyboard shown after displaying dictionary definition."""
    return InlineKeyboardMarkup([
        [
            InlineKeyboardButton("📜 Etymology", callback_data=f"etymology_{word}")
        ],
        [
            InlineKeyboardButton("🔍 Look up another word", callback_data="open_dictionary")
        ],
        [
            InlineKeyboardButton("🏠 Home", callback_data="home")
        ]
    ])

def speed_keyboard():
    """0.5x / 1x / 2x submenu with a back arrow."""
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🐌 0.5x", callback_data="speed_0.5"),
         InlineKeyboardButton("1x",      callback_data="speed_1.0"),
         InlineKeyboardButton("🐇 2x",   callback_data="speed_2.0")],
        [InlineKeyboardButton("← Back",  callback_data="close_speed")]
    ])


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🌍 Choose target language", callback_data="choose_language")],
        [InlineKeyboardButton("📖 Dictionary",             callback_data="open_dictionary")],
        [InlineKeyboardButton("ℹ️ About", callback_data="about")]
        ]
    await update.message.reply_text(
        text="What would you like to do?",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    # Snapshot target_lang NOW — we flip it after sending, but still need the old value for the button label
    target_lang = context.user_data.get('target_lang', 'fr')

    # Download voice message
    voice_file = await update.message.voice.get_file()

    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp:
        await voice_file.download_to_drive(tmp.name)
        context.user_data["last_audio"] = tmp.name

        # --- Transcribe ---
        transcribe_msg = await update.message.reply_text("⏳ Transcribing...")
        input_text = translator.transcribe(tmp.name)

        detected_lang_code = translator.get_source_language()
        detected_lang_name = LANGUAGES.get(detected_lang_code, detected_lang_code)

        await transcribe_msg.edit_text(f"⏳ Transcribing...\n{detected_lang_name}")
        await transcribe_msg.edit_text(f"*{detected_lang_name}* ➡️\n{input_text}", parse_mode="Markdown")

        # --- Translate ---
        translate_msg = await update.message.reply_text("⏳ Translating...")
        translated_text = translator.translate(input_text, target_language=target_lang)

        # Check if target language is non-Latin
        if target_lang in NON_LATIN_LANGS:
            latin = latinise(translated_text, target_lang)
            if latin:
                final_text = (
                    f"➡️ *{LANGUAGES[target_lang]}*\n"
                    f"{translated_text}\n\n"
                    f"_{latin}_\n\n"
                    f"⏳ Generating audio..."
                )
            else:
                final_text = (
                    f"➡️ *{LANGUAGES[target_lang]}*\n{translated_text}\n"
                    f"⏳ Generating audio...")
        else:
            final_text = (
                f"➡️ *{LANGUAGES[target_lang]}*\n"
                f"{translated_text}\n"
                f"⏳ Generating audio..."
                )

        await translate_msg.edit_text(final_text, parse_mode="Markdown")

        output_audio, sr = translator.translate_speech(
            audio_path=tmp.name,
            text=input_text,
            target_language=target_lang
        )

        output_path = "output.wav"
        sf.write(output_path, output_audio, sr)
        context.user_data["last_audio_translated"] = output_path

        # --- After audio is ready, remove "⏳ Generating audio..." but keep Latinisation
        # We can rebuild the message without the loading text
        if target_lang in NON_LATIN_LANGS and latin:
            clean_text = (
                f"➡️ *{LANGUAGES[target_lang]}*\n"
                f"{translated_text}\n\n"
                f"_{latin}_"
            )
        else:
            clean_text = f"➡️ *{LANGUAGES[target_lang]}*\n{translated_text}"

        await translate_msg.edit_text(clean_text, parse_mode="Markdown")

        # --- Store state for buttons / speed menu ---
        context.user_data["last_target_lang"] = target_lang          # e.g. "fr"
        context.user_data["last_detected_lang"] = detected_lang_code # e.g. "en"

        # --- Store last translation for possible later use ---
        context.user_data["last_translated_text"] = translated_text
        context.user_data["last_translated_lang"] = target_lang

        # --- Send audio + all buttons in one message ---
        # "Reply in X" label = target_lang (old target, e.g. French — what they'll speak next)
        # "Reply in X" callback = detected_lang_code (e.g. English — what to translate INTO)
        await update.message.reply_voice(
            voice=open(output_path, 'rb'),
            caption="What would you like to do next?",
            reply_markup=post_translate_keyboard(
                last_detected_lang=detected_lang_code
            )
        )

async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if context.args:
        lang = context.args[0]
        context.user_data['target_lang'] = lang
        await update.message.reply_text(f"✅ Target language set to: {lang}")
    else:
        await update.message.reply_text("Usage: /translate [language_code]")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("TEXT HANDLER FIRED")
    print("awaiting_dictionary_word =", context.user_data.get("awaiting_dictionary_word"))
    print("RAW TEXT =", repr(update.message.text))
    
    if context.user_data.get("awaiting_dictionary_word"):
        word = update.message.text.strip().lower()
        context.user_data["awaiting_dictionary_word"] = False
        context.user_data["last_dictionary_word"] = word  # Store for etymology button

        formatted_message = format_for_telegram(word, max_defs_per_pos=5)
        await update.message.reply_text(
            formatted_message, 
            parse_mode="Markdown",
            reply_markup=dictionary_result_keyboard(word)
        )

async def handle_buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "choose_language":
        reply_markup = build_language_keyboard(LANGUAGES, buttons_per_row=2)
        # Can't edit a voice message's text — send a new message instead
        await query.message.reply_text(
            text="🌍 Choose your target language:",
            reply_markup=reply_markup
        )

    elif query.data.startswith("lang_"):
        lang_code = query.data.replace("lang_", "")
        context.user_data["target_lang"] = lang_code

        if query.message.text:
            # Came from the language picker (text message) — collapse it in place
            await query.edit_message_text(text=f"Translating to {LANGUAGES[lang_code]}.\nSend a voice note or text.")
        else:
            # Came from the voice message caption ("Reply in" button) — can't edit that,
            # so just send the prompt as a new message
            await query.message.reply_text(f"Translating to {LANGUAGES[lang_code]}.\nSend a voice note or text.")

    # --- Speed submenu: open ---
    elif query.data == "open_speed":
        await query.edit_message_reply_markup(reply_markup=speed_keyboard())

    # --- Speed submenu: back arrow restores the post-translate buttons ---
    elif query.data == "close_speed":
        translate_into = context.user_data.get("last_detected_lang", "en")

        await query.edit_message_reply_markup(
            reply_markup=post_translate_keyboard(
                last_detected_lang=translate_into
            )
        )

    # --- Speed submenu: actual speed change ---
    elif query.data.startswith("speed_"):
        factor = float(query.data.split("_")[1])

        prev_audio_path = context.user_data.get("last_audio_translated")
        sr = 16000

        if prev_audio_path is None:
            await query.message.reply_text("⚠️ No translated audio available to modify.")
            return

        modified_audio = change_speed(prev_audio_path, factor, sr)

        output_path = "speed_changed.wav"
        sf.write(output_path, modified_audio, sr)
        await query.message.reply_voice(open(output_path, "rb"))

    elif query.data == "home":
        keyboard = [
            [InlineKeyboardButton("🌍 Choose target language", callback_data="choose_language")],
            [InlineKeyboardButton("📖 Dictionary", callback_data="open_dictionary")],
            [InlineKeyboardButton("ℹ️ About", callback_data="about")]
            ]

        await query.message.reply_text(
            text="🏡 Home",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif query.data == "open_dictionary":
        # Can't edit a voice message's text — send a new message instead
        await query.message.reply_text("📖 Send me a word to define (text or voice).")
        context.user_data["awaiting_dictionary_word"] = True

    elif query.data.startswith("etymology_"):
        word = query.data.replace("etymology_", "")
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

    elif query.data == "about":
        about_text = (
            "🤖 *hermes*\n\n"
            "A multilingual speech-to-speech translation bot powered by state-of-the-art AI models.\n\n"
            "🌍 Choose your target language and send a voice note or text to translate.\n"
            "🎧 Receive translated audio with options to adjust speed and more.\n\n"
            "Developed by Alex Dimmock.\n"
            "https://github.com/alexdimmock95/hermes/tree/main"
        )

        await query.message.reply_text(about_text, parse_mode="Markdown")

def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("translate", set_language))
    app.add_handler(CallbackQueryHandler(handle_buttons))
    app.add_handler(MessageHandler(filters.VOICE, handle_voice))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    print("🤖 Bot is running...")
    app.run_polling()


def build_language_keyboard(lang_map, buttons_per_row=3):
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


def change_speed(audio_path: str, speed_factor: float, sr: int):
    audio, _ = librosa.load(audio_path, sr=sr)

    vt = VoiceTransformer()
    modified_audio = vt.transform_voice(
        audio, sr,
        age_shift=speed_factor
    )

    return modified_audio


if __name__ == '__main__':
    main()

# TODO: Clean up architecture, eg put buttons in own script etc
### TODO: Add in the voice distortion, male female options in forst set of buttons, "voice effects"
###### TODO: Add in capability to press "pronunciation" or "syntax" for IPA, tongue position/shape info and word type, grammar info, respectively. ALSO ETYMOLOGY
            ##### Pronunciation: ability to press either link text/button to hear pronunciation of IPA item
### TODO/ language aware wiktionary - if detected language is french, wiktionary french version
##### TODO: if input speech/text messae is one word, automatically open up dictionary defenition with pronunciation
### TODO: What other models other than xtts can I use? Ones that are ideally faster, more languages

## python -m src.telegram_bot ##