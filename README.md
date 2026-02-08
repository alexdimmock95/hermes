# hermes

A near-real-time audio pipeline for accent softening that combines noise suppression, ASR alignment, and linguistically-informed DSP processing to subtly modify speech characteristics.

## Project Overview

This project builds a modular, laptop-friendly audio processing pipeline that:
- Accepts microphone or file input
- Performs lightweight noise suppression
- Uses ASR for phoneme alignment and multilingual transcription
- Applies DSP-based accent softening (formant nudges, pitch smoothing, energy normalization)
- Enables voice transformation (gender/age modification) using WORLD vocoder
- Supports multilingual speech-to-speech translation with voice cloning
- Includes comprehensive testing and metrics tracking
- **Telegram Bot**: Interactive Telegram bot for voice translation and in-chat dictionary lookups (`src/telegram_bot.py`)
- **Wiktionary client**: Robust wikitext parsing (via `mwparserfromhell`) for dictionary lookups and Telegram-safe formatting
- Lazy-loading for large models (WhisperX, XTTS) and improved demo/test coverage

## Project Structure

### Root Level Files

- **[README.md](README.md)** — This file; project documentation
- **[requirements.txt](requirements.txt)** — Python dependencies (numpy, scipy, soundfile, torch, whisper, librosa, pytest, etc.)

### Source Code (`src/`)

Core modules implementing the audio processing pipeline:

- **[asr.py](src/asr.py)** — Automatic Speech Recognition integration using Whisper for phoneme/word alignment and transcription
- **[denoiser.py](src/denoiser.py)** — Audio denoising module (RNNoise or torchaudio-based noise suppression)
- **[voice_transformer.py](src/voice_transformer.py)** — WORLD vocoder-based voice transformation for gender/age modification and STFT-based formant shifting with vowel-specific adjustments
- **[speech_to_speech.py](src/speech_to_speech.py)** — Multilingual speech-to-speech translation with voice cloning using WhisperX, Google Translate, and XTTS v2
- **[input_streamer.py](src/input_streamer.py)** — Real-time audio input handling with chunking, buffering, and overlap management
- **[overlap_add.py](src/overlap_add.py)** — Overlap-add reconstruction for seamless audio stitching with crossfade handling
- **[__pycache__/](__pycache__)** — Python bytecode cache (auto-generated)

### Tests (`tests/`)

Comprehensive test suite with pytest:

- **[test_asr.py](tests/test_asr.py)** — Unit tests for ASR module (phoneme extraction, timing accuracy)
- **[test_denoiser.py](tests/test_denoiser.py)** — Tests for denoising module (SNR metrics, audio quality)
- **[test_formant_shifting.py](tests/test_formant_shifting.py)** — Tests for formant modification DSP (frequency response, artifact detection)
- **[test_phonemise.py](tests/test_phonemise.py)** — Tests for phoneme-level processing and alignment
- **[test_streamer.py](tests/test_streamer.py)** — Tests for input streaming (jitter handling, buffering, chunking)
- **[test_voice_transformer.py](tests/test_voice_transformer.py)** — Tests for voice transformation (gender/age modification, formant warping using WORLD vocoder)
- **[test_speech_to_speech.py](tests/test_speech_to_speech.py)** — Tests for multilingual speech-to-speech translation with voice cloning

### Demo (`demo/`)

- **[demo.py](demo.py)** — Demo script showcasing end-to-end pipeline usage (file or mic input, output playback)

### Telegram Bot

A friendly Telegram bot for multilingual speech-to-speech translation and dictionary lookups.

- Core flow: voice note → WhisperX transcription → Google Translate → XTTS v2 voice-cloned synthesis
- Features:
  - Language picker and `/translate [lang_code]` command
  - "Reply in X" button to flip source/target for conversational workflows
  - Speed presets (0.5x / 1x / 2x) and on-the-fly speed changes from the UI
  - Dictionary lookups with formatted definitions and etymology (Wiktionary)
  - Non-Latin languages display a latinised preview for easier reading
- Run the bot:
  1. Add `TELEGRAM_BOT_TOKEN=...` to a `.env` file at the project root (or set the env var)
  2. Start the bot: `python src/telegram_bot.py` or `python -m src.telegram_bot`
- Notes:
  - Large models (WhisperX / XTTS) are lazy-loaded; expect initial latency on first use
  - Ensure a current `TELEGRAM_BOT_TOKEN` and network access for Wiktionary and translation APIs

### Audio Data (`audio_files/`)

Directory structure for managing audio input/output:

- **`input/`** — Input audio files for processing
  - **`temp_file_asr/`** — Temporary files for ASR processing
- **`output/`** — Final processed audio output
- **`spectrograms/`** — Spectrogram visualizations and analysis plots
- **`temp/`** — General temporary processing files

## ML Pronunciation Scorer

This bot includes a **machine learning pronunciation scorer** that evaluates 
user pronunciation using:

- **Audio Feature Extraction**: 13 Mel-frequency cepstral coefficients (MFCCs)
- **Deep Learning**: Facebook's Wav2Vec2 model for phoneme recognition
- **Alignment**: Dynamic Time Warping (DTW) for sequence alignment
- **Evaluation**: Combined acoustic + recognition scoring

### Technical Details

**Model Architecture:**
- Pre-trained Wav2Vec2-Base-960h (transformer-based)
- 95M parameters
- Fine-tuned on LibriSpeech dataset

**Features:**
- 16kHz audio sampling
- 13 MFCC coefficients
- Frame length: 25ms
- Hop length: 10ms

**Metrics:**
- DTW Distance (acoustic similarity)
- Phoneme Accuracy (speech recognition)
- Overall Score (weighted combination)

**Performance:**
- Model load time: ~10 seconds (first time)
- Inference time: ~5 seconds per word
- Accuracy: ~85% correlation with human ratings (estimated)

### Example Usage

\`\`\`python
from src.ml.pronunciation_scorer import score_user_pronunciation

# Score user's pronunciation
result = score_user_pronunciation(user_audio_bytes, "hello")

print(f"Score: {result['overall_score']}/100")
print(f"Feedback: {result['feedback']}")
\`\`\`

## Dependencies

Key Python packages (see [requirements.txt](requirements.txt)):

- **Audio I/O**: soundfile, sounddevice
- **DSP**: numpy, scipy, librosa, resampy, pyworld
- **ASR**: whisperx (WhisperX)
- **TTS / Voice Cloning**: TTS (Coqui XTTS v2)
- **Translation**: deep_translator (GoogleTranslator)
- **Bot & Config**: python-telegram-bot, python-dotenv
- **Dictionary / Parsing**: mwparserfromhell, requests
- **Phonemization**: phonemizer
- **ML Runtime**: onnxruntime
- **Testing**: pytest, psutil

## Getting Started

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Run tests:**
   ```bash
   pytest tests/
   ```

3. **Run the demo:**
   ```bash
   python demo/demo.py
   ```

## Architecture

The pipeline follows a modular, streaming-first design:

1. **Input Streaming** → Chunks and buffers audio from file or microphone
2. **Denoising** → Suppresses background noise while preserving speech
3. **ASR Alignment** → Extracts phoneme-level timing for precision modification
4. **Accent Softening** → Applies formant, pitch, and energy adjustments via DSP
5. **Overlap-Add Reconstruction** → Stitches chunks with minimal artifacts