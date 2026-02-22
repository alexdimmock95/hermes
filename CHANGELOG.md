# Changelog

All notable changes to the hermes project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- **Phoneme Correction Tips** — Pair-based articulation feedback in pronunciation scoring:
  - `PHONEME_CORRECTION_TIPS` dictionary mapping `(heard_phoneme, target_phoneme)` pairs to specific guidance
  - Tips are language-aware: a Spanish speaker saying 'B' instead of 'V' gets different guidance than a German speaker making the same mistake
  - Covers TH sounds, R variants (trill/tap/English), V vs B, W vs V, SH/ZH/CH/J, NG, vowel length, and schwa
  - Falls back to generic `ARTICULATION_TIPS` when no specific pair match found
  - Falls back to bare phoneme names when neither dictionary has an entry

---

## [0.6.1] — 2026-02-22

### Added
- **CI/CD Pipeline with GitHub Actions** — Automated testing on every push and pull request:
  - Docker-based test environment using `continuumio/miniconda3` to replicate local conda environment exactly
  - `environment.yml` generated via `conda env export --from-history` for clean, portable dependency spec
  - Docker layer caching with `docker/build-push-action` keyed on `environment.yml` hash — normal code pushes skip the 4+ minute install and go straight to tests in ~30 seconds
  - 22-test pytest suite covering core logic, handlers, imports, and database
  - `pytest.ini` with `asyncio_mode = auto` for clean async test support
  - Results visible on GitHub Actions tab with pass/fail per commit
- **About Section Language Support** — Updated `/about` command to document per-feature language coverage:
  - Text translation: any language via Google Translate
  - Voice-to-voice: the 18 XTTS-supported languages listed explicitly
  - Pronunciation scoring: 13 languages (Wav2Vec2 model coverage)
  - Smart Synonyms (CEFR): 13 languages
  - Voice effects: any language
  - Credits section separating Coqui XTTS (voice TTS) from Google TTS (text TTS)

### Changed
- Switched CI approach from pip-based to Docker-based after irresolvable dependency conflicts between whisperx (requires numpy>=2.0.2), deepfilternet and gruut (require numpy<2.0), and 20+ other packages with pinned versions
- whisperx excluded from CI environment (too problematic in Linux CI; tested locally)
- `sys.modules` pre-registration used in handler tests to block heavy ML imports before module load, replacing unreliable `patch()` path resolution

### Technical Notes
- Docker image is ~10GB due to torch, TTS, and ML model dependencies
- Cache upload is slow on first run but subsequent runs restore from cache in seconds
- flake8 not yet installed in Docker environment — linting step removed from workflow pending fix

---

## [0.6.0] — 2026-02-19

### Added
- **Performance Metrics & Latency Tracking** — Comprehensive timing instrumentation:
  - `PronunciationScore` class: Stage-by-stage timing (audio loading, MFCC extraction, DTW, speech recognition, phoneme analysis)
  - `SpeechToSpeechTranslator` class: Pipeline metrics (transcription, translation, synthesis breakdown)
  - Context managers for timing code blocks with millisecond precision
  - Debug mode toggle for detailed performance output
  - Time allocation percentages and bottleneck identification
  - Metrics accessible via API return values or `.get_last_metrics()`

- **Multi-language Pronunciation Scoring** — Language-specific speech recognition and phoneme analysis:
  - Language-specific Wav2Vec2 models for 13+ languages (English, French, Spanish, German, Italian, Portuguese, Russian, Polish, Japanese, Chinese, Arabic, Turkish, Dutch)
  - Dynamic model loading based on target language (e.g., `facebook/wav2vec2-large-xlsr-53-french` for French)
  - Language-specific IPA phoneme extraction using espeak-ng with correct language voices
  - Fixes critical bug where all pronunciations were scored against English phonemes
  - Scorer caching with automatic language switching (`get_scorer(language="fr")`)
  - Proper TTS reference generation in target language for accurate comparison

- **Bilingual Dictionary Definitions** — Native language definitions alongside English:
  - `fetch_bilingual_definitions()` function to query both English and native Wiktionaries
  - `format_bilingual_for_telegram()` for side-by-side display with flag emojis
  - Support for native Wiktionary section names (e.g., "Italiano" on it.wiktionary.org)
  - Fallback to English-only if native definitions unavailable

- **Enhanced Verb Conjugation Display** — Complete conjugation tables like Google Translate:
  - Full person conjugations for all tenses (je/tu/il/nous/vous/ils for French)
  - Support for all major tenses: Present, Future, Imperfect, Passé Simple, Conditional, Subjunctive
  - Clean table format grouped by tense with proper headers
  - Language-specific person labels (je/tu for French, yo/tú for Spanish, etc.)
  - Extraction functions updated for French, Spanish, Italian, Portuguese, Romanian

### Changed
- **Dictionary Definition Parsing** — Improved wikitext cleaning and extraction:
  - Better handling of template removal (inflection templates, label templates)
  - Shorter minimum definition length (3 chars instead of 10) to capture brief definitions
  - Enhanced extraction of definitions from `{{lb}}` and `{{inflection of}}` templates
  - Fixed Jaccard similarity calculation and phoneme comparison logic

- **Bot Navigation & UX** — Improved message history and keyboard consistency:
  - Added `keep_history` parameter to `safe_message_update()` for preserving dictionary definitions
  - Home button added to language selection screen and speed menu
  - Dictionary definitions remain visible in chat history when navigating
  - Updated all navigation handlers to optionally preserve message history

- **Pronunciation Scoring Display** — Enhanced user feedback:
  - Better formatting of conjugation tables in Telegram
  - Markdown escaping for all displayed text
  - Clearer section headers and person labels

### Fixed
- Critical bug: Pronunciation scoring now uses correct language models (French words scored with French phonemes, not English)
- Dictionary parsing for short definitions and vulgar terms
- Template cleaning in definition extraction
- Pronunciation audio generation using wrong language for TTS
- Division by zero errors in similarity calculations

---

## [0.5.5] — 2026-02-14

### Added
- Word form buttons after dictionary lookup (Conjugations / Plural form / Comparative forms) shown with definition

### Changed
- README focused on Telegram bot, dictionary, and learning; removed obsolete real-time pipeline emphasis
- CHANGELOG: project name, Next Steps trimmed of irrelevant items

---

## [0.5.0] — 2026-02-09

### Added
- **Word Statistics & Learning Progress** — Track and display user learning metrics:
  - Database storage for learning events (src/learning/storage.py)
  - Aggregation module for computing statistics (word frequency, learning streaks, pronunciation scores)
  - New bot callbacks for retrieving and displaying progress data
  - Learning event tracking system for vocabulary acquisition monitoring
- **Enhanced Pronunciation Scoring** — Integration of ML pronunciation scorer with Telegram bot:
  - Phoneme-level accuracy feedback
  - User pronunciation comparison with native speakers
  - Scoring history and progress tracking
- **Dictionary Feature Enhancements** — Refined dictionary lookup and integration:
  - Improved wiktionary client robustness and parsing
  - Better etymology and definition formatting for Telegram
  - Enhanced error handling and fallback mechanisms

### Changed
- Refactored dictionary and pronunciation modules for better modularity and testing
- Improved learning event storage and retrieval efficiency
- Enhanced Telegram bot handlers with new `/stats` and learning-related commands
- Updated keyboard layouts to include new learning progress buttons

### Fixed
- Dictionary parsing edge cases and formatting issues
- Learning event aggregation accuracy
- Minor UI/UX improvements in Telegram bot

---

## [0.4.0] — 2026-02-01

### Added
- **Telegram Bot** — Interactive Telegram bot for voice-based translation and in-chat dictionary lookup
  - Voice note processing: WhisperX transcription → Google Translate → XTTS v2 voice-cloned synthesis
  - Post-translation UI: reply-in language button, speed presets (0.5x / 1x / 2x), and language picker
  - Auto-flip of the next target language based on detected source language for conversational flow
- **Wiktionary client** — Robust wikitext-based dictionary lookup using `mwparserfromhell` and Telegram-safe formatting
- **SpeechToSpeechTranslator improvements** — Lazy-loading of WhisperX and XTTS models, improved language detection, and simplified API
- **Telegram integration of `VoiceTransformer`** — Speed / age modification via bot controls and accessible voice transform presets
- **Demo updates & tests** — Updated demo workflow, added/expanded tests for speech-to-speech, voice transformation, and dictionary lookups

### Changed
- Improved error handling and robustness across ASR, TTS, and dictionary modules
- README updated to document Telegram bot and dictionary features

### Fixed
- Wiktionary fetching/parsing robustness and request headers (User-Agent)
- Minor bugfixes and stability improvements

---

## [0.3.0] — 2026-01-29

### Added
- **VoiceTransformer class** — WORLD vocoder-based voice transformation with pitch, formant, and time-stretch modifications
  - Gender conversion presets (male→female, female→male)
  - Age modification presets (older, younger)
  - Customizable gender shift (semitones), age shift (time-stretch ratio), and formant shift (spectral envelope ratio)
- **FormantShifter class** — Enhanced STFT-based formant shifting with vowel-specific modifications
  - Spectral envelope warping for vowel-specific formant nudges
  - Crossfade blending for smooth transitions
  - Spectrogram visualization capabilities
- **SpeechToSpeechTranslator class** — Complete speech-to-speech translation pipeline
  - WhisperX integration for multilingual ASR with voice alignment
  - Google Translate for text translation
  - XTTS v2 for multilingual voice cloning synthesis
  - End-to-end pipeline: speech → text → translation → voice-cloned speech
- Unit tests for voice transformation (test_voice_transformer.py)
- Unit tests for speech-to-speech translation (test_speech_to_speech.py)
- Updated demo.py to showcase voice transformation and translation capabilities

### Changed
- Expanded project scope to include voice transformation and multilingual speech translation
- Enhanced demo pipeline to demonstrate full accent softening and voice modification workflows

---

## [0.2.0] — 2025-12-24

### Added
- **FormantShifter class** — DSP module for formant shifting and accent softening
- **Formant shifting integration** into demo pipeline
- Unit tests for formant shifting functionality
- Updated demo to showcase full accent softening pipeline

### Changed
- Enhanced demo.py to demonstrate end-to-end formant modification
- Improved test coverage for DSP transformations

---

## [0.1.2] — 2025-12-24

### Added
- **ASR phoneme timestamp extraction** — Implemented phoneme-level timing from Whisper
- ASR wrapper class for audio transcription with alignment data
- Unit tests for ASR module with phoneme verification
- phoneme_output.json output format for ASR results

### Changed
- Updated demo to include ASR phoneme extraction
- Enhanced ASRWrapper with detailed timing information

---

## [0.1.1] — 2025-12-14

### Added
- **ASRWrapper class** — Wrapper around Whisper for audio transcription
- Unit tests for ASR wrapper functionality
- Initial implementation of phoneme extraction from ASR output

---

## [0.1.0] — 2025-12-12

### Added
- **Denoiser module** — Audio denoising functionality with noise suppression
- **Overlap-add reconstruction** — Seamless audio stitching with overlap handling
- Unit tests for denoising and overlap-add modules
- Enhanced demo script with denoising pipeline
- Audio quality metrics tracking

### Changed
- Improved input streaming for better chunk handling
- Enhanced demo with full denoising + reconstruction workflow

### Features
- SNR (Signal-to-Noise Ratio) metrics calculation
- Crossfade blending for chunk reconstruction
- Minimal latency overlap-add implementation

---

## [0.0.1] — 2025-12-06

### Added
- **Initial commit** — Project scaffolding and core setup
- **FileStreamer class** — Audio file input handling with chunking
- **Basic demo script** — End-to-end pipeline demonstration
- Project structure with src/, tests/, and demo/ directories
- requirements.txt with core dependencies
- Initial test suite framework

### Features
- Audio file reading and chunking
- Basic pipeline architecture
- Test infrastructure with pytest

---

## Project Milestones

- **Week 0** — Setup & smoke test (Initial commit, FileStreamer, demo) [COMPLETE]
- **Week 1** — Input streamer (FileStreamer with chunking and buffering) [COMPLETE]
- **Week 2** — Denoiser integration (Denoiser module, SNR tests) [COMPLETE]
- **Week 3** — ASR alignment (ASRWrapper with phoneme timestamps) [COMPLETE]
- **Week 4** — Accent softening (FormantShifter DSP module) [COMPLETE]
- **Week 5** — Recombiner + metrics (Enhanced overlap-add, latency tracking) [COMPLETE]
- **Week 6** — Tests + CI + documentation (Full test suite, README, CI setup) [COMPLETE]

---

## Version History Summary

| Version | Date | Focus | Status |
|---------|------|-------|--------|
| Unreleased | — | Phoneme correction tips | In progress |
| 0.6.1 | Feb 22, 2026 | CI/CD Pipeline & About section language docs | Complete |
| 0.6.0 | Feb 19, 2026 | Latency Metrics & Multi-language Pronunciation | Complete |
| 0.5.5 | Feb 14, 2026 | Dictionary Elements | Complete |
| 0.5.0 | Feb 9, 2026 | Learning Analytics & Pronunciation Scoring Enhancements | Complete |
| 0.4.0 | Feb 1, 2026 | Telegram Bot & Speech-to-Speech Translation | Complete |
| 0.3.0 | Jan 29, 2026 | Voice Transformation & WORLD Vocoder Integration | Complete |
| 0.2.0 | Dec 24, 2025 | Formant Shifting & Accent Softening DSP | Complete |
| 0.1.2 | Dec 24, 2025 | ASR Phoneme Extraction & Timing | Complete |
| 0.1.1 | Dec 14, 2025 | ASR Wrapper Implementation | Complete |
| 0.1.0 | Dec 12, 2025 | Denoising & Overlap-Add Reconstruction | Complete |
| 0.0.1 | Dec 6, 2025 | Initial Project Setup & FileStreamer | Complete |

---

## Development Timeline

**Dec 6** — Project initialization with FileStreamer and basic demo  
**Dec 12** — Denoiser and overlap-add reconstruction added  
**Dec 14** — ASR wrapper implementation for transcription  
**Dec 24** — ASR phoneme timing extraction and FormantShifter DSP module  
**Jan 26, 2026** — README and project documentation completed  
**Jan 29, 2026** — Voice transformation and speech-to-speech classes added  
**Feb 1, 2026** — Telegram bot v1 release with speech-to-speech translation  
**Feb 2-4, 2026** — Dictionary functionality enhancements and bot UX improvements  
**Feb 8-9, 2026** — Word statistics, learning progress tracking, and pronunciation scoring integration  
**Feb 14, 2026** — Added functionality within dictionary for word forms: verb conjugations, plural and superlative forms of lemmas  
**Feb 18-19, 2026** — Multi-language pronunciation scoring, bilingual dictionary definitions, complete verb conjugation tables, comprehensive performance metrics and latency tracking  
**Feb 22, 2026** — CI/CD pipeline with GitHub Actions (Docker-based), about section language documentation, pair-based phoneme correction tips

---

## Next Steps

- [ ] Add capability to press "pronunciation" or "syntax" for IPA, tongue position/shape info and word type, grammar info, respectively