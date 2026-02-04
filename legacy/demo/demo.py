"""
Main demo / workflow entry point for the Accent Softener pipeline.

This script orchestrates the full end-to-end audio processing flow
on a single, full-length waveform (non-streaming).

Pipeline overview:
1. Load audio from disk (mono, float32)
2. Broadband denoising on the full signal
3. ASR transcription with phoneme-level alignment
4. Identification of vowel phonemes for selective processing
5. Formant shifting applied only to detected vowel regions
6. Optional global pitch / voice transformation
7. Write processed audio to disk

Design constraints & assumptions:
- All DSP operates on the full waveform (no chunking / streaming)
- Phoneme alignment is used to localise transformations in time
- Vowel-only formant shifting to minimise artefacts and preserve intelligibility
- Temporary files are written for ASR compatibility
- CPU-only inference assumed (configurable)

This file is intentionally procedural:
it acts as a reference implementation and debugging harness,
not as a production API or streaming system.
"""


import sys
import numpy as np
import soundfile as sf
from pathlib import Path


# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))
from src.denoiser import Denoiser
from src.asr import PhonemeAligner
from src.voice_transformer import FormantShifter, VoiceTransformer
from src.speech_to_speech import SpeechToSpeechTranslator

def main():
    print("Accent Softener")
    print("=" * 50)
    
    # Define input and output paths
    input_file = Path("audio_files/input/test.wav")
    output_folder = Path("audio_files/output")
    output_folder.mkdir(parents=True, exist_ok=True)

    # Define temp path
    temp_folder = Path("audio_files/temp")
    temp_folder.mkdir(parents=True, exist_ok=True)
    
    if not input_file.exists():
        print(f"ERROR: File not found: {input_file}")
        return
    
    # ============================================================
    # STEP 1: LOAD AUDIO
    # ============================================================
    print("\n" + "="*50)
    print("STEP 1: Load Audio")
    print("="*50)
    
    audio, sr = sf.read(input_file)
    print(f"  File: {input_file.name}")
    print(f"  Sample rate: {sr} Hz")
    print(f"  Original shape: {audio.shape}")
    
    # Ensure mono
    if audio.ndim > 1:
        print("  Converting stereo to mono...")
        audio = np.mean(audio, axis=1)
    
    audio = audio.flatten().astype(np.float32)
    print(f"  Duration: {len(audio)/sr:.2f} seconds")
    print(f"  ✓ Audio loaded")

    # ============================================================
    # STEP 2: DENOISE
    # ============================================================
    print("\n" + "="*50)
    print("STEP 2: Denoise Audio")
    print("="*50)
    
    denoiser = Denoiser(model_name="DeepFilterNet3", post_filter=True)
    audio = denoiser.process_frame(audio)
    print("  ✓ Denoising complete")

    # ============================================================
    # STEP 3: ASR TRANSCRIPTION & PHONEME ALIGNMENT
    # ============================================================
    print("\n" + "="*50)
    print("STEP 3: ASR Transcription & Phoneme Alignment")
    print("="*50)

    # --- 3.1 Save denoised audio to temp file ---
    temp_asr_file = temp_folder / f"{input_file.stem}_tempasr{input_file.suffix}"
    sf.write(temp_asr_file, audio, sr)

    # --- 3.2 Initialise phoneme aligner ---
    aligner = PhonemeAligner(
        device="cpu",
        model_size="base",
        compute_type="int8",
        batch_size=16
    )

    aligner.load_models()

    # --- 3.3 Run ASR + alignment ---

    result, vowel_phonemes = aligner.process(str(temp_asr_file))

    print(f"\nTranscription Result:\n'{result.text}'\n")
    print(f"Detected Vowel Phonemes: {len(vowel_phonemes)}")

    for vp in vowel_phonemes:
        print(f"  {vp['phoneme']} | start: {vp['start']:.3f}s end: {vp['end']:.3f}s")

    print("✓ ASR + phoneme alignment complete")

    # ============================================================
    # STEP 4: FORMANT SHIFTING 
    # ============================================================
    print("\n" + "="*50)
    print("STEP 4: Formant Shifting")
    print("="*50)

    # --- Instantiate the formant shifter ---
    shifter = FormantShifter(
        sr=sr,
        n_fft=1024,
        hop_length=256,
        win_length=1024,
        max_freq=4000,
        multiplier=1
    )

    # Duplicate audio for shifting
    audio_shifted = audio.copy()

    vowel_phonemes = [p for p in vowel_phonemes if p['phoneme'] in shifter.vowel_shifts]

    print("\nDetected vowel phonemes:")
    
    for vp in vowel_phonemes:
        alpha = shifter.vowel_shifts.get(vp['phoneme'], 1.0)
        print(f"  {vp['phoneme']}  |  start: {vp['start']:.3f}s  end: {vp['end']:.3f}s  word: {vp['word']}  alpha: {alpha}")

    # --- Apply formant shift to all detected vowel phonemes ---
    for vp in vowel_phonemes:
        # Shift vowel using the alpha from the dictionary
        shifted_segment = shifter.shift_formants_vowel(audio_shifted, vp)

        start_s = int(vp['start'] * sr)
        end_s = start_s + len(shifted_segment)

        audio_shifted[start_s:end_s] = shifter.crossfade(
            original=audio_shifted[start_s:end_s],
            shifted=shifted_segment,
            fade_len=int(0.02 * sr)  # 20 ms crossfade
        )

    print("\n✓ Formant shifting complete")

    ##### This is the limit of what formant shifting will do. Need to refer to chatgpt advice on LPC approach, and cross referencing this against praat for accuracy.
    #### Think its called WORLD 

    ## TODO: Add choice to go either pitch shift or coqui

    # ============================================================
    # STEP 5: PROCESSING MODE SELECTION
    # ============================================================
    print("\n" + "="*50)
    print("STEP 5: Select Processing Mode")
    print("="*50)
    
    print("\n1. Voice Transformation (Gender/Age modification)")
    print("2. Speech-to-Speech Translation (Multilingual voice cloning)")
    
    mode_choice = input("\nSelect mode (1-2): ").strip()
    
    if mode_choice == "1":
        # ============================================================
        # PITCH SHIFT
        # ============================================================
        print("\n" + "="*50)
        print("STEP 5: Pitch Shift")
        print("="*50)

        # Voice transformation menu
        print("\n" + "="*50)
        print("Options")
        print("="*50)
        print("\n1. Male → Female")
        print("2. Female → Male")
        print("3. Make Older")
        print("4. Make Younger")
        print("5. Custom Parameters")
        
        choice = input("\nSelect transformation (1-5): ").strip()
        
        transformer = VoiceTransformer()

        if choice == "1":
            print("\n[Processing] Male → Female transformation...")
            output_audio = transformer.preset_male_to_female(audio, sr)
        elif choice == "2":
            print("\n[Processing] Female → Male transformation...")
            output_audio = transformer.preset_female_to_male(audio, sr)
        elif choice == "3":
            print("\n[Processing] Older voice transformation...")
            output_audio = transformer.preset_older(audio, sr)
        elif choice == "4":
            print("\n[Processing] Younger voice transformation...")
            output_audio = transformer.preset_younger(audio, sr)
        elif choice == "5":
            print("\nCustom parameters:")
            gender_shift = float(input("  Gender shift (semitones, -12 to +12): "))
            formant_shift = float(input("  Formant shift (ratio, 0.7 to 1.3): "))
            age_shift = float(input("  Age shift (ratio, 0.7 to 1.3): "))

            print("\n[Processing] Custom transformation...")
            output_audio = transformer.transform_voice(
                audio, sr,
                gender_shift=gender_shift,
                formant_shift=formant_shift,
                age_shift=age_shift
            )
        else:
            print("\nInvalid choice. Using default (Male → Female)")
            output_audio = transformer.preset_male_to_female(audio, sr)
        
        print("Complete")

    elif mode_choice == "2":
        # ============================================================
        # STEP 6: TRANSLATION
        # ============================================================
        print("\n" + "="*50)
        print("STEP 6: Translation")
        print("="*50)

        # Initialize translator
        translator = SpeechToSpeechTranslator(
            device="cpu",
            model_size="base",
            compute_type="int8",
            batch_size=16
        )
        
        # Translate to French
        output_audio, sr = translator.translate_speech(
            audio_path=str(temp_asr_file),
            text=result.text,
            target_language="fr"
        )

        print("Complete")

    # ============================================================
    # FINAL STEP: SAVE OUTPUT
    # ============================================================
    print("\n" + "="*50)
    print("FINAL STEP: Save Output")
    print("="*50)
    
    output_file = output_folder / f"{input_file.stem}_processed.wav"

    sf.write(str(output_file), output_audio, samplerate=sr, format='WAV')
    
    print(f"\n  Output info:")
    print(f"    Shape: {audio.shape}")
    print(f"    Dtype: {audio.dtype}")
    print(f"    Sample rate: {sr}")
    print(f"    Path: {output_file}")
    
    # Statistics
    original_audio, _ = sf.read(input_file)
    if original_audio.ndim > 1:
        original_audio = np.mean(original_audio, axis=1)
    
    original_rms = np.sqrt(np.mean(original_audio**2))
    processed_rms = np.sqrt(np.mean(audio_shifted**2))
    
    print(f"\n  Statistics:")
    print(f"    Original RMS: {original_rms:.4f}")
    print(f"    Processed RMS: {processed_rms:.4f}")
    print(f"    RMS change: {((processed_rms/original_rms - 1)*100):+.1f}%")
    
    print(f"\n✓ Processing complete! Output saved to:")
    print(f"  {output_file.absolute()}")
    
    # ============================================================
    # OPTIONAL: Chunking for streaming
    # ============================================================
    # If you need to stream the output later, you can chunk it here
    # But DSP processing should already be done at this point

if __name__ == "__main__":
    main()