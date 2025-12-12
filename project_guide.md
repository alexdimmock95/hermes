# Accent Softening Pipeline — Project Plan & Code Scaffolds - ChatGPT

*Compact, runnable on a laptop, modular, testable. Built with Python only (no other languages).*

---

## 1. Project goal (brief)

Build a near-real-time audio pipeline that:

* accepts mic or file input
* performs lightweight noise suppression
* runs ASR for alignment
* applies linguistically informed DSP "accent softening" (formant nudges, pitch smoothing, energy normalisation)
* stitches output with minimal drift
* records latency/metrics and ships a pytest test-suite and a CI skeleton

This is a **DSP-first** project with ASR used for alignment and analysis (not full ML accent conversion). It’s laptop-friendly.

---

## 2. High-level milestones (6 weeks, iterative)

1. **Week 0 — Setup & smoke test**: env, basic audio I/O, chunking, play-back of reassembled audio.
2. **Week 1 — Input streamer**: robust chunking, buffering, overlap, test coverage for jitter.
3. **Week 2 — Denoiser integration**: RNNoise or torchaudio denoiser; SNR tests.
4. **Week 3 — ASR alignment**: Whisper-tiny offline chunked inference + phoneme/word timestamps.
5. **Week 4 — Accent softening (DSP)**: formant smoothing, pitch smoothing, energy normalisation; unit tests.
6. **Week 5 — Recombiner + metrics**: stitch chunks, crossfades, latency tracker, WER/SNR checks.
7. **Week 6 — Tests + CI + demo**: full pytest battery, GitHub Actions, README, demo script.

---

## 3. Environment & dependencies (minimal)

* Python 3.11+
* pipenv or venv + pip

Suggested packages (install with `pip install`):

* numpy, scipy
* soundfile (pysoundfile)
* sounddevice (for mic I/O) or pyaudio
* torchaudio, torch (cpu-first; GPU optional)
* onnxruntime (if using RNNoise ONNX)
* openai-whisper or whisperx (or `whisper` from -official)
* librosa (for STFT, pitch)
* resampy
* pyworld or pysptk (for formant / pitch tools) — optional but useful
* pytest

> **Note:** choose CPU-friendly model variants (whisper-tiny or small) so it runs on laptop.

---

## 4. Folder structure

```
accent_softener/
├─ src/
│  ├─ input_streamer.py
│  ├─ denoiser.py
│  ├─ asr_wrapper.py
│  ├─ accent_softener.py
│  ├─ recombiner.py
│  ├─ metrics.py
│  └─ utils.py
├─ tests/
│  ├─ test_streamer.py
│  ├─ test_denoiser.py
│  ├─ test_asr.py
│  ├─ test_accent_softener.py
│  └─ integration_test.py
├─ demo/
│  └─ demo_stream.py
├─ requirements.txt
└─ README.md
```

---

## 5. Module scaffolds + explanations

Below are **minimal scaffolds** for each module. Each block includes: purpose, inputs/outputs, and a small code skeleton (not full impl). Use these as the scaffold to iterate with tests.

### `src/input_streamer.py`

**Purpose:** capture mic or read file, chunk into frames with overlap, yield frames with metadata (timestamp, seq).

```python
# src/input_streamer.py
"""Streamer: yields (frame_bytes, timestamp, seq)

Design notes:
- Use numpy arrays of shape (n_samples,)
- chunk_size ~ 160ms (e.g., 160ms @ 16kHz = 2560 samples)
- overlap e.g., 20-50ms
- provide buffering to smooth jitter
"""

import numpy as np
import soundfile as sf

class FileStreamer:
    def __init__(self, path, sr=16000, chunk_ms=160, overlap_ms=40):
        self.path = path
        self.sr = sr
        self.chunk = int(sr * chunk_ms / 1000)
        self.overlap = int(sr * overlap_ms / 1000)
        self._buffer = None

    def frames(self):
        wav, _ = sf.read(self.path)
        # ensure mono, resample outside or here
        pos = 0
        seq = 0
        while pos < len(wav):
            end = pos + self.chunk
            frame = wav[pos:end]
            # pad short frames
            if len(frame) < self.chunk:
                frame = np.pad(frame, (0, self.chunk - len(frame)))
            yield frame, seq
            pos += self.chunk - self.overlap
            seq += 1
```

**Explanation:**

* Keep it simple: yield numpy arrays. Tests will verify expected sequence lengths and overlap behaviour.

---

### `src/denoiser.py`

**Purpose:** lightweight noise suppression per frame. Prefer ONNX RNNoise or torchaudio denoising.

```python
# src/denoiser.py
"""Simple adapter for a denoiser model.

Design notes:
- Provide a Denoiser class with `process(frame: np.ndarray) -> np.ndarray`
- Keep state if model needs it
- Provide synchronous CPU fallback
"""

import numpy as np

class Denoiser:
    def __init__(self, model_path=None):
        # load ONNX or torch model here
        self.model_path = model_path

    def process(self, frame: np.ndarray) -> np.ndarray:
        # placeholder: identity pass-through
        return frame
```

**Explanation:**

* Start with an identity pass-through to test pipeline; then swap in RNNoise ONNX inference code. Keep tests to check SNR improvement using test fixtures.

---

### `src/asr_wrapper.py`

**Purpose:** run Whisper-tiny (or chosen ASR), return word timestamps and confidence for alignment.

```python
# src/asr_wrapper.py
"""Run chunked ASR and provide alignment info.

Design notes:
- Use whisper or whisperx (whisperx adds forced alignment)
- Provide `transcribe_chunk(frame, sr)` -> list of (word, start, end, conf)
- Keep batching logic outside
"""

from typing import List, Tuple

class ASRWrapper:
    def __init__(self, model_name='tiny'):
        # load whisper model here
        self.model_name = model_name

    def transcribe_chunk(self, frame: bytes, sr=16000) -> List[Tuple[str,float,float,float]]:
        # return placeholder
        return []
```

**Explanation:**

* On laptop use tiny model; ensure you cache model and reuse. Tests should assert predictable alignment on a fixed sample.

---

### `src/accent_softener.py`

**Purpose:** implement DSP operations per frame: formant smoothing, pitch smoothing, energy normalisation.

```python
# src/accent_softener.py
"""DSP-based accent softener.

Design notes:
- Each transform should be testable independently
- Provide a pipeline class `AccentSoftener` exposing `process(frame, sr, alignment)`
- `alignment` is optional metadata from ASR to optionally guide stronger processing near vowels
"""

import numpy as np

class AccentSoftener:
    def __init__(self, sr=16000):
        self.sr = sr

    def _pitch_smooth(self, frame: np.ndarray) -> np.ndarray:
        # rough placeholder
        return frame

    def _formant_nudge(self, frame: np.ndarray) -> np.ndarray:
        # rough placeholder
        return frame

    def process(self, frame: np.ndarray, alignment=None) -> np.ndarray:
        x = self._pitch_smooth(frame)
        x = self._formant_nudge(x)
        # energy normalisation
        return x
```

**Explanation:**

* Each helper will be expanded: use `pyworld` or `librosa` to extract F0, spectral envelope, and push formants slightly toward neutral targets. Keep changes subtle to avoid artefacts.

---

### `src/recombiner.py`

**Purpose:** stitch processed frames, crossfade overlaps, maintain timestamp integrity.

```python
# src/recombiner.py
import numpy as np

class Recombiner:
    def __init__(self, chunk, overlap):
        self.chunk = chunk
        self.overlap = overlap
        self.buffer = np.zeros(0, dtype=np.float32)

    def append(self, frame: np.ndarray) -> np.ndarray:
        # naive: append and return when we have at least one chunk
        self.buffer = np.concatenate([self.buffer, frame])
        if len(self.buffer) >= self.chunk:
            out = self.buffer[:self.chunk]
            self.buffer = self.buffer[self.chunk - self.overlap:]
            return out
        return None
```

**Explanation:**

* Later refine with windowed crossfades to remove clicks.

---

### `src/metrics.py`

**Purpose:** collect per-module latency, CPU usage, SNR, WER. Expose simple APIs to log and export JSON.

```python
# src/metrics.py
import time, json

class Metrics:
    def __init__(self):
        self.data = []

    def record(self, name, start, end, extra=None):
        self.data.append({'name': name, 'lat_ms': (end-start)*1000, 'extra': extra or {}})

    def export(self, path='metrics.json'):
        with open(path, 'w') as f:
            json.dump(self.data, f, indent=2)
```

**Explanation:**

* Add CPU measurements using `psutil` if needed. Collect WER by comparing ASR transcripts pre/post-processing.

---

## 6. Testing + CI

* Use `pytest` and small audio fixtures (a few seconds, multiple noise types).
* Integration test runs: file -> full pipeline -> output length sanity -> SNR/WER delta checks.
* GitHub Actions: run `pytest -q` on PRs. Use caching for wheel builds.

*GH Actions skeleton (workflow snippet in repo).*

---

## 7. First dev tasks (day 1)

1. Create repo and venv, add requirements.
2. Implement `FileStreamer` and a `demo_stream.py` that reads a file and writes back reassembled audio.
3. Write `test_streamer.py` to validate chunk sizes and overlap.
4. Push to GitHub, add README explaining aims and how to run.

---

## 8. Risks & mitigation (short)

* **Artefacts from formant shifting**: keep nudges tiny; write perceptual tests; A/B demo.
* **Latency spikes**: measure per-module; provide fallbacks (bypass heavy modules)
* **ASR misalignment**: use forced aligners like `whisperx` or `gentle` if needed but start with chunk-level timestamps.

---

## 9. Next step (actionable)

I created the repo scaffold in the document above. **Tell me which module you want to implement first** (I recommend `input_streamer.py`).

I'll provide a step-by-step implementation plan for that module with code snippets, tests, and debugging tips. 🙌🔥

---

*If you want, I can also export a `requirements.txt` and a demo audio file generator in the next message.*


# Claude

This is a **really solid learning project**! Here's my honest assessment:

## What's excellent ✨

1. **Right scope for learning** - DSP-first approach is perfect. You'll understand the fundamentals before diving into heavy ML, and it'll actually run on your laptop.

2. **Smart architectural choices**:
   - Modular design makes debugging easy
   - Test coverage from day 1 (many audio projects skip this!)
   - Metrics built in (you'll *see* what's working)

3. **Realistic constraints** - Acknowledging laptop limitations and starting with CPU inference shows good planning

4. **Incremental milestones** - Each week adds one piece. You can stop at week 3 and still have a working denoiser+ASR pipeline.

## Suggestions to make it even better 🎯

### 1. **Add a "Week -1" for audio fundamentals**
Before coding, spend a few days with:
- Generate and visualize sine waves, white noise
- Manually apply a low-pass filter and *hear* the difference  
- Use `librosa.display.specshow()` to look at spectrograms
- **Why**: You'll understand what your code is doing to waveforms

### 2. **Simplify the ASR scope initially**
- Week 3 is ambitious with "phoneme-level timestamps"
- **Easier path**: Start with Whisper's word-level timestamps (built-in), *then* add phoneme alignment in week 5 if you want
- WhisperX is great but adds complexity early

### 3. **Make the accent softening more concrete**
Right now "formant nudges" is vague. Consider picking **one specific target** to learn deeply:
- Example: "Reduce th→f substitution in Indian English" 
  - Detect /θ/ using phoneme alignment
  - Apply high-frequency boost at 4-8kHz during those segments
- **Why**: Vague goals → vague learning. Specific problems teach specific DSP techniques.

### 4. **Add perceptual evaluation earlier**
Week 6 has "demo script" but add in Week 4:
```python
# Simple A/B comparison tool
def compare(original, processed):
    """Play both, ask user which sounds better"""
    # Later: Add PESQ or STSE metrics
```
You need **ears-on feedback** as you develop, not just at the end.

### 5. **Risk mitigation is too brief**
The "artefacts from formant shifting" risk is real! Add:
- **Week 4.5**: "Artefact detection sprint"
  - Generate test cases with known issues (robotic voice, phase cancellation)
  - Add spectral flatness checks in metrics.py
  - Build a "safety bypass" if distortion > threshold

## What to watch out for ⚠️

1. **Overlap-add is tricky** - Your `recombiner.py` will need proper windowing (Hann/Hamming) or you'll get clicks. Budget extra time here.

2. **"Accent softening" can become a rabbit hole** - Formant tracking with `pyworld` is finicky. If Week 4 drags, don't be afraid to simplify to *just* pitch smoothing first.

3. **16kHz is low for formant work** - Consider 22050 or 24000 Hz. Phone speech is 8kHz, but for vowel quality you want more resolution.

## Modified week structure (my suggestion)

```
Week -1: Audio fundamentals playground (NumPy + librosa experiments)
Week 0: Setup + streaming pipeline (no processing yet)
Week 1: Add RNNoise, verify with SNR tests
Week 2: ASR integration (word-level only)
Week 3: Pick ONE accent feature (e.g., pitch contour smoothing)
Week 4: Implement that feature with A/B perceptual tests
Week 5: Recombiner refinement + latency optimization  
Week 6: Second accent feature OR polish + CI + docs
```

## Final verdict 🎯

**This is a great project.** You'll learn:
- Real-time audio processing constraints
- DSP fundamentals (filters, spectral processing)
- How to test non-deterministic pipelines  
- The gap between "works in isolation" and "works in a system"

The plan is maybe 15% overscoped (phoneme alignment + formant shifting is a lot), but that's fine—you can cut scope and still learn tons.

---

**Your next step should be**: 
1. Set up the repo
2. Implement `input_streamer.py` 
3. Write a **5-line test** that proves you can chunk audio and reconstruct it bit-perfectly (before any processing)

Want me to give you that test code + a sample audio generator so you can validate the streamer works? That's the foundation everything else builds on.