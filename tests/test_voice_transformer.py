import librosa
import sys
import soundfile as sf
from pathlib import Path

# Add src directory to path
src_path = Path(__file__).parent.parent / "src"
sys.path.insert(0, str(src_path))

from voice_transformer import VoiceTransformer

# ---- Load test audio ----
audio_path = "/Users/Alex/Documents/Coding/personal_project/accent_softener/audio_files/input/test_nonoise.wav"
audio, sr = librosa.load(audio_path, sr=None)

# Define output directory
OUTPUT_DIR = "output/tests/voice_transformer"

def test_male_to_female():
    """Test male → female transformation"""
    print("\n" + "="*50)
    print("Testing: Male → Female")
    print("="*50)

    print(f"Loaded audio: {len(audio)} samples at {sr} Hz")
    
    # Transform
    transformer = VoiceTransformer()
    output = transformer.preset_male_to_female(audio, sr)
    
    # Save
    output_path = f"{OUTPUT_DIR}/male_to_female.wav"
    sf.write(output_path, output, sr)
    print("✓ Saved to output/male_to_female.wav")

def test_female_to_male():
    """Test female → male transformation"""
    print("\n" + "="*50)
    print("Testing: Female → Male")
    print("="*50)
    
    print(f"Loaded audio: {len(audio)} samples at {sr} Hz")
    
    transformer = VoiceTransformer()
    output = transformer.preset_female_to_male(audio, sr)
    
    output_path = f"{OUTPUT_DIR}/female_to_male.wav"
    sf.write(output_path, output, sr)
    print(f"✓ Saved to {output_path}")

def test_older():
    """Test making voice sound older"""
    print("\n" + "="*50)
    print("Testing: Older voice")
    print("="*50)
    
    print(f"Loaded audio: {len(audio)} samples at {sr} Hz")
    
    transformer = VoiceTransformer()
    output = transformer.preset_older(audio, sr)
    
    output_path = f"{OUTPUT_DIR}/older.wav"
    sf.write(output_path, output, sr)
    print(f"✓ Saved to {output_path}")

def test_younger():
    """Test making voice sound younger"""
    print("\n" + "="*50)
    print("Testing: Younger voice")
    print("="*50)
    
    print(f"Loaded audio: {len(audio)} samples at {sr} Hz")
    
    transformer = VoiceTransformer()
    output = transformer.preset_younger(audio, sr)
    
    output_path = f"{OUTPUT_DIR}/younger.wav"
    sf.write(output_path, output, sr)
    print(f"✓ Saved to {output_path}")

if __name__ == "__main__":
    import os
    
    # Create output directory
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Run tests
    print("\nVoice Transformer Tests\n")
    
    # Comment out tests you don't have audio for
    test_male_to_female()
    #test_female_to_male()
    test_older()
    test_younger()
    
    print("\n" + "="*50)
    print("All tests complete.")
    print("="*50)