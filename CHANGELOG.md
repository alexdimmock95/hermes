# Changelog

All notable changes to the Accent Softener project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [Unreleased]

### Added
- Ongoing refinements and optimization

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
- **Week 5** — Recombiner + metrics (Enhanced overlap-add, latency tracking) [IN PROGRESS]
- **Week 6** — Tests + CI + documentation (Full test suite, README, CI setup) [IN PROGRESS]

---

## Version History Summary

| Version | Date | Focus | Status |
|---------|------|-------|--------|
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

---

## Next Steps

- [x] UI for interaction on a dashboard
- [x] Development of this on an app, see if possible to run this externally on phone
- [ ] Integration of real-time use (real time audio input, not real time translation due to latencies of translate and tts modules)
- [ ] Enhanced metrics tracking and latency profiling
- [ ] Real-time microphone input streaming
- [ ] Advanced pitch smoothing algorithms
- [ ] Energy normalization and loudness matching
- [ ] CI/CD pipeline setup (GitHub Actions)
- [ ] Audio quality benchmarks and comparisons
- [ ] Add in capability to press "pronunciation" or "syntax" for IPA, tongue position/shape info and word type, grammar info, respectively.
- [ ] language aware wiktionary - if detected language is french, wiktionary french version
- [ ] What other models other than xtts can I use? Ones that are ideally faster, more languages
- [ ] is there a way to do proper formant shifting to change accent using DTW modification? 
- [ ] dictionary mode > look up word (english) > translate to target language > show definition in target language, with option to show english definition as well. Dictionary in multiple languages not picking words even in their correct spelling and language. 
- [ ] if the text/voice translate input is one word, show the {target lang}.wiktionary definition of that word
- [ ] flesh out language capability - explain that for translation there are x, within dictionary there are y, there are always different offerings
- [ ] when user searches a word in dictionary, have button to (if verb) conjugations, (if noun) other variations of the lemma, (if adjective) comparative/superlative forms, etc.
- [ ] ensure response messages from the dictionary or translator stay in the message thread. so that new ones come in on new messages, then stay there
- [ ] no module named langdetect