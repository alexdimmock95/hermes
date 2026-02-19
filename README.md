# hermes

A Telegram bot for multilingual voice and text translation, in-chat dictionary lookups with bilingual definitions, and learning tools (pronunciation practice with language-specific models, word statistics, performance metrics).

## Project Overview

The bot is the main interface. It provides:

- **Translation** — Voice note or text → WhisperX transcription → Google Translate → XTTS v2 voice-cloned audio. Language picker, "Reply in X" for conversational flow, speed presets (0.5x / 1x / 2x). Performance metrics available in debug mode.

- **Dictionary** — Bilingual Wiktionary lookups with definitions in both English and native language (e.g., French + English for French words), etymology, examples, and **word-form buttons** (complete conjugation tables for verbs with all tenses and persons, plural for nouns, comparative/superlative for adjectives). Pronunciation audio, etymology, practice pronunciation with language-specific models, and Smart Synonyms (CEFR) where supported.

- **Learning** — Event storage, word stats, multi-language pronunciation scoring (Wav2Vec2 + DTW with language-specific models), and `/stats` for progress. Pronunciation scoring uses correct phoneme models per language (French words scored with French phonemes, not English).

- **Performance** — Comprehensive latency tracking and metrics available in debug mode across all major components (transcription, translation, synthesis, pronunciation scoring). Identifies bottlenecks and timing breakdowns.

Under the hood it uses: **speech_to_speech** (WhisperX, Google Translate, XTTS with latency metrics), **voice_transformer** (speed/age/gender presets), **wiktionary_client** (mwparserfromhell, bilingual lookups, Telegram-safe formatting), **learning** (SQLite, aggregations), **ml/pronunciation_score** (multi-language Wav2Vec2 models, language-specific IPA extraction).

## Project Structure

### Root

- **[README.md](README.md)** — This file
- **[requirements.txt](requirements.txt)** — Python dependencies
- **[CHANGELOG.md](CHANGELOG.md)** — Version history and changes

### Source (`src/`)

- **[telegram_bot.py](src/telegram_bot.py)** — Bot entry point and routing
- **[speech_to_speech.py](src/speech_to_speech.py)** — Voice/text translation with performance metrics (WhisperX, Translate, XTTS)
- **[voice_transformer.py](src/voice_transformer.py)** — Speed/age/gender voice effects
- **[latiniser.py](src/latiniser.py)** — Latin script conversion for non-Latin languages

#### Telegram Bot (`src/telegram_bot/`)

- **[handlers.py](src/telegram_bot/handlers.py)** — Commands and message handlers (translate, dictionary, pronunciation practice)
- **[callbacks.py](src/telegram_bot/callbacks.py)** — Button callbacks (language selection, word forms, pronunciation, etymology, etc.)
- **[keyboards.py](src/telegram_bot/keyboards.py)** — Inline keyboard layouts with universal Home button
- **[config.py](src/telegram_bot/config.py)** — Languages and bot configuration
- **[utils.py](src/telegram_bot/utils.py)** — Utility functions (speed adjustment, etc.)

#### Dictionary (`src/dictionary/`)

- **[wiktionary_client.py](src/dictionary/wiktionary_client.py)** — Bilingual definitions (English + native), etymology, examples, word-forms keyboard, improved template parsing
- **[corpus_examples.py](src/dictionary/corpus_examples.py)** — Sentence examples from corpora
- **[cefr.py](src/dictionary/cefr.py)** — CEFR difficulty classification / Smart Synonyms
- **[word_forms_extractor.py](src/dictionary/word_forms_extractor.py)** — Complete conjugation tables (all tenses, all persons), plural forms, comparative/superlative forms

#### Learning (`src/learning/`)

- **[storage.py](src/learning/storage.py)** — SQLite for learning events
- **[events.py](src/learning/events.py)** — Event models
- **[aggregations.py](src/learning/aggregations.py)** — Statistics and trends

#### ML (`src/ml/`)

- **[pronunciation_score.py](src/ml/pronunciation_score.py)** — Multi-language Wav2Vec2-based pronunciation scoring with language-specific models, IPA extraction, comprehensive performance metrics

### Tests (`tests/`)

pytest suite for ASR, denoiser, formant shifting, phonemize, streamer, voice_transformer, speech_to_speech.

### Demo

- **Pipeline demo** — Optional: `python legacy/demo/demo.py` (file or mic → processing → playback), if that script is present.

## Running the Bot

1. Add `TELEGRAM_BOT_TOKEN=...` to a `.env` file at the project root (or set the env var).
2. Start the bot:
```bash
   python src/telegram_bot.py
```
   or
```bash
   python -m src.telegram_bot
```

3. **Enable Debug Mode** (optional) for detailed performance metrics:
```python
   # In your code
   translator = SpeechToSpeechTranslator(debug=True)
   scorer = PronunciationScore(language="fr", debug=True)
```

Notes: WhisperX and XTTS are lazy-loaded (first use may be slower). Language-specific Wav2Vec2 models download on first use per language. You need network access for Wiktionary and translation APIs.

## Getting Started (development)

1. **Install dependencies**
```bash
   pip install -r requirements.txt
```

2. **Install espeak-ng** (required for IPA phoneme extraction):
```bash
   # macOS
   brew install espeak-ng
   
   # Linux
   sudo apt-get install espeak-ng
```

3. **Run tests**
```bash
   pytest tests/
```

4. **Run the demo** (optional, if present)
```bash
   python legacy/demo/demo.py
```

## Dependencies

Key packages: **python-telegram-bot**, **python-dotenv**, **whisperx**, **TTS** (XTTS), **deep_translator**, **mwparserfromhell**, **gtts**, **soundfile**, **librosa**, **torch**, **transformers** (Wav2Vec2), **fastdtw**, **langdetect**, **mlconjug3** (conjugations), **inflect** (plurals). See [requirements.txt](requirements.txt).

## Features

### Multi-language Pronunciation Scoring

The pronunciation scorer now uses **language-specific models** to ensure accurate scoring:

- **Language-specific Wav2Vec2 models**: French words scored with French phoneme recognition, Spanish with Spanish, etc.
- **13+ languages supported**: English, French, Spanish, German, Italian, Portuguese, Russian, Polish, Japanese, Chinese, Arabic, Turkish, Dutch
- **Language-specific IPA extraction**: Uses espeak-ng with correct language voices
- **Proper TTS reference**: Generates reference audio in target language for fair comparison

Example:
```python
from src.ml.pronunciation_score import score_user_pronunciation

# Score French pronunciation
result = score_user_pronunciation(
    user_audio_bytes, 
    "bonjour",
    language="fr",  # Uses French models!
    debug=True
)
print(result['overall_score'], result['feedback'])
```

### Bilingual Dictionary

Dictionary lookups now show definitions in **both English and the native language**:

- English Wiktionary definitions (reliable, comprehensive)
- Native language definitions (e.g., French definitions from fr.wiktionary.org)
- Flag emojis for visual distinction (🇬🇧 English, 🇫🇷 French, etc.)
- Automatic fallback if native definitions unavailable

### Complete Verb Conjugations

Word form buttons now display **complete conjugation tables** like Google Translate:

- All persons: je/tu/il/nous/vous/ils (French), yo/tú/él/nosotros/vosotros/ellos (Spanish), etc.
- All major tenses: Present, Future, Imperfect, Passé Simple, Conditional, Subjunctive
- Clean table format grouped by tense
- Supports French, Spanish, Italian, Portuguese, Romanian conjugations

### Performance Metrics

Both translation and pronunciation scoring include **comprehensive latency tracking** in debug mode:

**Speech-to-Speech Translation:**
```
📊 COMPLETE PIPELINE METRICS
⏱️  STAGE BREAKDOWN:
├─ Transcription: 3.621s
├─ Translation: 0.342s
├─ Synthesis: 7.781s
└─ TOTAL PIPELINE: 11.744s

📊 TIME ALLOCATION:
   Transcription: 30.8%
   Translation: 2.9%
   Synthesis: 66.2%  ← Bottleneck identified!
```

**Pronunciation Scoring:**
```
⏱️  PERFORMANCE METRICS
├─ Audio loading: 45.2ms
├─ MFCC extraction: 123.7ms
├─ DTW computation: 89.3ms
├─ Speech recognition: 1847.2ms  ← 78.9% of total time
├─ Phoneme analysis: 234.1ms
└─ TOTAL TIME: 2.341s
```

Access metrics programmatically:
```python
# Translation metrics
(audio, sr), metrics = translator.translate_speech(
    audio_path, 
    target_language="fr",
    return_metrics=True
)

# Or access last metrics
metrics = translator.get_last_metrics()
print(f"Synthesis took: {metrics['synthesis']['synthesis_time']:.2f}s")
```

## Learning Analytics

- Events stored in `data/learning_events.db`.
- Aggregations: words learned/reviewed, pronunciation scores, streaks, trends.
- `/stats`: dashboard, difficult words, weekly/monthly progress.
- Multi-language pronunciation scoring with language-specific models ensures accurate feedback.

## ML Pronunciation Scorer

- **Language-specific Wav2Vec2 models** for accurate phoneme recognition per language
- **DTW** (Dynamic Time Warping) for temporal alignment
- **MFCC** acoustic features for audio comparison
- **Language-specific IPA extraction** using espeak-ng with correct voices
- **Comprehensive performance metrics** in debug mode
- Used by the "Practice Pronunciation" flow in the bot
- Example:
```python
  from src.ml.pronunciation_score import score_user_pronunciation
  
  # Score French pronunciation (uses French models!)
  result = score_user_pronunciation(
      user_audio_bytes, 
      "courais",
      language="fr",
      debug=True
  )
  print(result['overall_score'], result['feedback'])
  
  # Access performance metrics
  if result.get('metrics'):
      print(f"Speech recognition: {result['metrics']['speech_recognition_time']:.2f}s")
```

## Architecture Highlights

- **Lazy loading**: Models load on first use to minimize startup time
- **Language-specific models**: Pronunciation scoring automatically selects correct Wav2Vec2 model per language
- **Bilingual dictionary**: Queries both English and native Wiktionaries for comprehensive definitions
- **Performance instrumentation**: Context managers and timing decorators throughout codebase
- **Caching**: Scorer and model instances cached with automatic language switching
- **Message history preservation**: Dictionary definitions remain visible while navigating
- **Universal navigation**: Home button accessible from all major screens

## Recent Improvements (v0.6.0)

1. **Multi-language pronunciation scoring** - Fixed critical bug where all languages were scored against English phonemes
2. **Bilingual dictionary** - Native + English definitions side-by-side
3. **Complete conjugations** - Full verb tables with all tenses and persons
4. **Performance metrics** - Comprehensive latency tracking and bottleneck identification
5. **Improved parsing** - Better handling of short definitions, templates, and special characters
6. **Enhanced UX** - Message history preservation, universal Home button, better keyboard layouts

See [CHANGELOG.md](CHANGELOG.md) for complete version history.