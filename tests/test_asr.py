"""
Standalone behaviour test for ASR wrapper.
"""

import sys
from pathlib import Path
import soundfile as sf
import numpy as np

sys.path.append(str(Path(__file__).parent.parent))
from src.asr import ASRWrapper


def load_audio(path: Path):
    audio, sr = sf.read(path)

    # Limit to first N seconds
    max_seconds = 5 # seconds
    audio = audio[: int(max_seconds * sr)]

    # Ensure float 32
    if audio.dtype != np.float32:
        audio = audio.astype(np.float32)

    return audio, sr

def main():
    audio_path = Path("/Users/Alex/Documents/Coding/personal_project/accent_softener/audio_files/input/sat_plans.wav")

    # Check if file exists
    if not audio_path.exists():
        print(f"ERROR: Audio file not found at {audio_path}")
        return

    audio, sr = load_audio(audio_path)

    print("Audio shape:", audio.shape)
    print("Audio dtype:", audio.dtype)
    print("Original sample rate:", sr)

    asr = ASRWrapper(model_name="tiny")
    print("Model loaded")

    print("Transcribing...")
    result = asr.transcribe_full(audio, sr=sr)
    
    print("\n" + "="*50)
    print(f"Number of words/segments returned: {len(result)}")
    print("="*50)

    if len(result) == 0:
        print("WARNING: ASR returned no words")
        print("Possible reasons:")
        print("  - Audio file is silent or too quiet")
        print("  - Audio duration is too short")
        print("  - Audio format issue")
        return
    
    # Print first 5 words
    print("\nFirst 5 words:")
    for i, (word, start, end, conf) in enumerate(result[:5]):
        print(f"  {i+1}. '{word}' [{start:.2f}s - {end:.2f}s] (confidence: {conf:.3f})")

    # Run structural assertions
    print("\nRunning structural tests...")
    
    # Structure: must be a list
    assert isinstance(result, list), "ASR did not return a list"
    print("✓ Result is a list")

    # Non-empty
    assert len(result) > 0, "ASR returned an empty word list"
    print("✓ Result is non-empty")

    # Check first element structure
    w0 = result[0]
    assert isinstance(w0, tuple) and len(w0) == 4, "Each item should be a 4-tuple"
    print("✓ Each item is a 4-tuple")

    word, start, end, conf = w0

    # Word checks
    assert isinstance(word, str) and word.strip() != "", "Invalid word format"
    print("✓ Word is a non-empty string")

    # Timing checks
    assert start < end, "Start time must be < end time"
    assert start >= 0, "Start time can't be negative"
    print("✓ Timing values are valid")
    
    assert 0 <= conf <= 1, "Confidence must be between 0 and 1"
    print("✓ Confidence is in valid range [0, 1]")

    # Type checks
    assert audio.dtype == np.float32, "Audio must be float32"
    print("✓ Audio dtype is float32")

    print("\n" + "="*50)
    print("ALL TESTS PASSED! ✓")
    print("="*50)
    
    # Print full transcription
    print("\nFull transcription:")
    full_text = " ".join([word for word, _, _, _ in result])
    print(f"  \"{full_text}\"")

if __name__ == "__main__":
    main()