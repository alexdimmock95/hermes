import pytest
whisperx = pytest.importorskip("whisperx", reason="whisperx not available in CI")

import sys
import soundfile as sf
from pathlib import Path

# Add src to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from speech_to_speech import SpeechToSpeechTranslator

def test_translation():
    """Test speech-to-speech translation to French"""
    
    print("\n" + "="*70)
    print("Testing Speech-to-Speech Translation")
    print("="*70)
    
    # Initialize translator
    translator = SpeechToSpeechTranslator(device="cpu", model_size="base")
    
    # Translate to French
    audio_path = "/Users/Alex/Documents/Coding/personal_project/accent_softener/audio_files/input/sat_plans.wav"
    output, sr = translator.translate_speech(
        audio_path=audio_path,
        target_language="fr"
    )

    # Save output
    output_dir = Path("output/tests/speech_to_speech")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    output_file = output_dir / "translated_fr.wav"
    sf.write(output_file, output, sr)
    
    print(f"\nTest complete! Saved to: {output_file}")

if __name__ == "__main__":
    test_translation()