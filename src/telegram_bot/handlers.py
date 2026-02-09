"""Handler functions for the Telegram bot."""

from telegram import Update
from telegram.ext import ContextTypes
import tempfile
import soundfile as sf
import librosa

from src.telegram_bot.config import LANGUAGES
from src.telegram_bot.keyboards import (
    post_translate_keyboard,
    dictionary_result_keyboard,
    home_keyboard
)

from src.telegram_bot.config import LANGUAGES, WIKTIONARY_LANGUAGES  # ← Add WIKTIONARY_LANGUAGES
from src.telegram_bot.utils import change_speed
from src.speech_to_speech import SpeechToSpeechTranslator
from src.voice_transformer import VoiceTransformer
from src.dictionary.wiktionary_client import format_for_telegram, format_etymology_for_telegram
from src.latiniser import latinise, NON_LATIN_LANGS
from src.ml.pronunciation_score import score_user_pronunciation
from src.learning.events import emit_word_event


# Initialize translator
translator = SpeechToSpeechTranslator(device="cpu", model_size="base")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /start command."""
    await update.message.reply_text(
        text="What would you like to do?",
        reply_markup=home_keyboard()
    )


async def set_language(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the /translate command to set target language."""
    if context.args:
        lang = context.args[0]
        context.user_data['target_lang'] = lang
        await update.message.reply_text(f"✅ Target language set to: {lang}")
    else:
        await update.message.reply_text("Usage: /translate [language_code]")


async def handle_voice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Main voice handler - routes to practice mode, voice effects, or translation based on context.
    """
    # Check if user is practicing a word
    practicing_word = context.user_data.get('practicing_word')
    
    if practicing_word:
        # They're in practice mode - score their pronunciation!
        await handle_pronunciation_scoring(update, context, practicing_word)
    elif context.user_data.get('mode') == 'voice_fx':
        # Voice effects mode - apply transformation
        await handle_voice_effects(update, context)
    else:
        # Normal voice message handling (translation)
        await handle_voice_translation(update, context)


async def handle_voice_effects(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Apply voice effects transformation to user's audio."""
    preset = context.user_data.get('voice_fx_preset')
    
    if not preset:
        await update.message.reply_text(
            "❌ No voice effect selected. Please choose one from the menu.",
            reply_markup=home_keyboard()
        )
        return
    
    # Download voice message
    voice_file = await update.message.voice.get_file()
    
    with tempfile.NamedTemporaryFile(suffix='.ogg', delete=False) as tmp:
        await voice_file.download_to_drive(tmp.name)
        
        # Send processing message
        status_msg = await update.message.reply_text(
            f"🎛 Applying *{preset.replace('_', ' ').title()}* effect...",
            parse_mode="Markdown"
        )
        
        try:
            # Load audio
            audio, sr = librosa.load(tmp.name, sr=None)
            
            # Initialize transformer and apply preset
            transformer = VoiceTransformer()
            
            if preset == "male_to_female":
                output_audio = transformer.preset_male_to_female(audio, sr)
                effect_name = "⬆️ Male → Female"
            elif preset == "female_to_male":
                output_audio = transformer.preset_female_to_male(audio, sr)
                effect_name = "⬇️ Female → Male"
            elif preset == "older":
                output_audio = transformer.preset_older(audio, sr)
                effect_name = "👴 Older"
            elif preset == "younger":
                output_audio = transformer.preset_younger(audio, sr)
                effect_name = "🧒 Younger"
            else:
                raise ValueError(f"Unknown preset: {preset}")
            
            # Save output
            output_path = "voice_fx_output.wav"
            sf.write(output_path, output_audio, sr)
            
            # Update status
            await status_msg.edit_text(
                f"✨ Transformation complete!\n\n*Effect:* {effect_name}",
                parse_mode="Markdown"
            )
            
            # Send transformed audio
            await update.message.reply_voice(
                voice=open(output_path, 'rb'),
                caption="🎤 Your transformed voice",
                reply_markup=home_keyboard()
            )
            
            # Clear voice effects mode
            context.user_data.pop("mode", None)
            context.user_data.pop("voice_fx_preset", None)
            
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            print(f"ERROR in voice effects: {error_details}")
            
            await status_msg.edit_text(
                f"❌ Error applying voice effect: {str(e)}\n\n"
                f"Please try again or choose a different effect.",
                reply_markup=home_keyboard()
            )


async def handle_voice_translation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle voice message translation (normal mode)."""
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


async def handle_pronunciation_scoring(
    update: Update, 
    context: ContextTypes.DEFAULT_TYPE,
    word: str
):
    """
    Score user's pronunciation attempt.
    """
    # Send "processing" message
    processing_msg = await update.message.reply_text(
        "🔄 Analyzing your pronunciation...\n"
        "This may take 5-10 seconds."
    )
    
    try:
        # Download user's voice message
        voice_file = await update.message.voice.get_file()
        voice_bytes = await voice_file.download_as_bytearray()
        
        # Score pronunciation using ML model
        from src.telegram_bot.callbacks import get_scorer
        scorer = get_scorer()
        
        result = score_user_pronunciation(
            bytes(voice_bytes),
            word,
            scorer=scorer,
            debug=True  # Set to True to include detailed debug info in the result (like DTW scores, recognized phonemes, etc.
        )
        
        # Format results
        score = result['overall_score']
        feedback = result['feedback']
        recognized = result['recognized_text']
        
        # Determine emoji based on score
        if score >= 90:
            emoji = "🌟"
        elif score >= 75:
            emoji = "✅"
        elif score >= 60:
            emoji = "👍"
        else:
            emoji = "💪"
        
        response = (
            f"{emoji} *Pronunciation Score: {score}/100*\n\n"
            f"*Target word:* {word}\n\n"
            f"*What I heard:* {recognized}\n"
            '''
            f"*Breakdown:*\n"
            f"• Acoustic similarity: {result['dtw_score']}/100\n"
            f"• Speech recognition: {result['phoneme_score']}/100\n\n"
            f"*Feedback:* {feedback}\n\n"
            '''
        )
        
        # Add phoneme analysis if available
        if result.get('phoneme_analysis'):
            pa = result['phoneme_analysis']
            response += (
                f"\n🔤 *Detailed Phoneme Analysis:*\n"
                f"Target sounds: `/{pa['target_ipa']}/`\n"
                f"Your sounds: `/{pa['user_ipa']}/`\n\n"
            )
            
            # Add specific phoneme feedback
            phoneme_feedback = pa.get('feedback', '')
            if phoneme_feedback and phoneme_feedback != "All sounds pronounced correctly! 🎉":
                response += f"{phoneme_feedback}\n"

        response += "\nTry again or choose another option:"

        keyboard = dictionary_result_keyboard(word)
        
        # Delete processing message and send results
        await processing_msg.delete()
        await update.message.reply_text(
            response,
            parse_mode="Markdown",
            reply_markup=keyboard
        )
        
        # Clear practice mode
        context.user_data.pop('practicing_word', None)
        
    except Exception as e:
        import traceback
        error_details = traceback.format_exc()
        print(f"ERROR in pronunciation scoring: {error_details}")
        
        await processing_msg.edit_text(
            f"❌ Error analyzing pronunciation: {str(e)}\n\n"
            f"Please try again or contact support if this persists."
        )
        context.user_data.pop('practicing_word', None)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages (primarily for dictionary lookups)."""
    
    if context.user_data.get("awaiting_dictionary_word"):
        word = update.message.text.strip().lower()
        context.user_data["awaiting_dictionary_word"] = False
        context.user_data["last_dictionary_word"] = word

        # Get the user's target language or default to English
        target_lang = context.user_data.get('target_lang', 'en')
        
        # Map to Wiktionary language name
        language = WIKTIONARY_LANGUAGES.get(target_lang, 'English')

        # Log the word search event
        user_id = update.effective_user.id
        emit_word_event(user_id, word, "dictionary")

        formatted_message = format_for_telegram(
            word, 
            language=language, 
            max_defs_per_pos=5
        )
        
        await update.message.reply_text(
            formatted_message, 
            parse_mode="Markdown",
            reply_markup=dictionary_result_keyboard(word)
        )
    else:
        # If not awaiting dictionary word, maybe inform user
        await update.message.reply_text(
            "I'm not sure what to do with that. Use the buttons or /start to begin.",
            reply_markup=home_keyboard()
        )