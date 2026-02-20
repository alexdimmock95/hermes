"""
Standalone test script for DeepFilterNet denoiser.
Tests different models and settings on your audio files.
"""

import sys
import numpy as np
import soundfile as sf
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))  # add project root
from legacy.src.denoiser import Denoiser

def main():
    print("DeepFilterNet Denoiser Test")
    print("=" * 50)
    
    # Load your real audio file
    input_file = Path("audio_files/input/youtube_noise.wav")
    
    if not input_file.exists():
        print(f"ERROR: File not found: {input_file}")
        print("Please update the path to your audio file.")
        return
    
    audio, sr = sf.read(input_file)
    
    print(f"\n[LOAD] Audio shape: {audio.shape}")
    print(f"[LOAD] Sample rate: {sr} Hz")
    
    # Ensure mono
    if audio.ndim > 1:
        print(f"[LOAD] Converting stereo to mono...")
        audio = np.mean(audio, axis=1)
    
    audio = audio.flatten().astype(np.float32)
    print(f"[LOAD] Final shape: {audio.shape}")
    print(f"[LOAD] Duration: {len(audio)/sr:.2f} seconds")
    
    # Test different models and configurations
    # Uncomment the ones you want to test
    models_to_test = [
        ("DeepFilterNet3", False),  # Best quality, default
        ("DeepFilterNet3", True),   # With aggressive post-filter
        # ("DeepFilterNet2", False),  # Faster, lower quality
        # ("DeepFilterNet", False),   # Original
    ]
    
    output_dir = Path("audio_files/test_output")
    output_dir.mkdir(parents=True, exist_ok=True)
    
    results = []
    
    for model_name, post_filter in models_to_test:
        print("\n" + "="*50)
        print(f"Testing: {model_name}" + (" (with post-filter)" if post_filter else ""))
        print("="*50)
        
        # Initialize denoiser
        denoiser = Denoiser(model_name=model_name, post_filter=post_filter)
        
        # Process entire file
        print("Denoising...")
        clean_audio = denoiser.process_frame(audio)
        
        # Save result
        suffix = "_pf" if post_filter else ""
        denoised_out = output_dir / f"{input_file.stem}_{model_name.lower()}{suffix}_denoised.wav"
        sf.write(str(denoised_out), clean_audio, sr)
        
        # Statistics
        original_rms = np.sqrt(np.mean(audio**2))
        denoised_rms = np.sqrt(np.mean(clean_audio**2))
        rms_change = ((denoised_rms/original_rms - 1)*100)
        
        print(f"\nStatistics:")
        print(f"  Original RMS: {original_rms:.4f}")
        print(f"  Denoised RMS: {denoised_rms:.4f}")
        print(f"  RMS change: {rms_change:+.1f}%")
        print(f"\n✓ Saved: {denoised_out}")
        
        # Store results for summary
        results.append({
            'model': model_name,
            'post_filter': post_filter,
            'rms_change': rms_change,
            'file': denoised_out
        })
    
    # Also save original for comparison
    original_out = output_dir / f"{input_file.stem}_original.wav"
    sf.write(str(original_out), audio, sr)
    print(f"\n✓ Original saved: {original_out}")
    
    # Print summary
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    for r in results:
        pf_text = " (post-filter)" if r['post_filter'] else ""
        print(f"{r['model']}{pf_text}: {r['rms_change']:+.1f}% RMS change")
    
    print(f"\nAll files saved to: {output_dir.absolute()}")

if __name__ == "__main__":
    main()