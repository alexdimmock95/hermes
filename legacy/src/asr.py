import torch
import warnings
import os
import json

# Suppress specific warning categories
warnings.filterwarnings('ignore', category=UserWarning)
warnings.filterwarnings('ignore', category=FutureWarning)
warnings.filterwarnings('ignore', category=DeprecationWarning)

# Set espeak library
os.environ['PHONEMIZER_ESPEAK_LIBRARY'] = '/opt/homebrew/Cellar/espeak-ng/1.52.0/lib/libespeak-ng.dylib'
os.environ['PHONEMIZER_ESPEAK_PATH'] = '/opt/homebrew/bin/espeak-ng'

# Monkey patch torch.load
_original_torch_load = torch.load
def _patched_torch_load(*args, **kwargs):
    kwargs.setdefault('weights_only', False)
    return _original_torch_load(*args, **kwargs)
torch.load = _patched_torch_load

import whisperx
from phonemizer import phonemize

# IPA vowels for filtering
IPA_VOWELS = {
    'i', 'ɪ', 'e', 'ɛ', 'æ', 'ɑ', 'ɒ', 'ɔ', 'o', 'ʊ', 'u',
    'ʌ', 'ə', 'ɚ', 'ɝ', 'a', 'ː', 'y', 'ø', 'œ'
}

class PhonemeAligner:
    """
    A class for transcribing audio and aligning phonemes with timestamps.
    
    Usage:
        aligner = PhonemeAligner(device="cpu", model_size="base")
        aligner.load_models()
        result = aligner.process("audio.wav")
        result.print_summary()
        result.export_json("output.json")
    """
    
    def __init__(self, device="cpu", model_size="base", compute_type="int8", batch_size=16):
        """
        Initialize the PhonemeAligner.
        
        Args:
            device (str): Device to run models on ("cpu" or "cuda")
            model_size (str): WhisperX model size ("tiny", "base", "small", "medium", "large")
            compute_type (str): Compute type for model ("int8", "float16", "float32")
            batch_size (int): Batch size for transcription
        """
        self.device = device
        self.model_size = model_size
        self.compute_type = compute_type
        self.batch_size = batch_size
        
        # Models (initialized as None, loaded later)
        self.model = None
        self.align_model = None
        self.align_metadata = None

    def load_models(self):
        """
        Load WhisperX transcription and alignment models.
        Call this once before processing audio files.
        """
        print(f"Loading {self.model_size} model on {self.device}...")
        self.model = whisperx.load_model(
            self.model_size, 
            self.device, 
            compute_type=self.compute_type, 
            language="en"
        )
        
        print("Loading alignment model...")
        self.align_model, self.align_metadata = whisperx.load_align_model(
            language_code="en", 
            device=self.device
        )
        
        print("✓ Models loaded successfully")
    
    def _transcribe(self, audio_file):
        """
        Internal method: Transcribe audio file.
        
        Args:
            audio_file (str): Path to audio file
            
        Returns:
            list: Transcription segments
        """
        if self.model is None:
            raise RuntimeError("Models not loaded. Call load_models() first.")
        
        audio = whisperx.load_audio(audio_file)
        transcription_result = self.model.transcribe(audio, batch_size=self.batch_size)
        
        # Handle both dict and list formats
        if isinstance(transcription_result, dict):
            return transcription_result["segments"], audio
        else:
            return transcription_result, audio
    
    def _align_words(self, segments, audio):
        """
        Internal method: Align words with timestamps.
        
        Args:
            segments (list): Transcription segments
            audio (np.array): Audio data
            
        Returns:
            list: Aligned segments with word-level timestamps
        """
        try:
            aligned_result = whisperx.align(
                segments, 
                self.align_model, 
                self.align_metadata, 
                audio, 
                self.device, 
                return_char_alignments=False
            )
            return aligned_result["segments"]
        except Exception as e:
            print(f"✗ Word alignment failed: {e}")
            print("  Continuing with segment-level timestamps only...")
            return segments
    
    def _phonemize_segments(self, segments):
        """
        Internal method: Convert words to phonemes and distribute across timestamps.
        
        Args:
            segments (list): Aligned segments
            
        Returns:
            list: Segments with phoneme timings
        """
        phoneme_data = []
        
        for segment in segments:
            segment_data = {
                'segment_text': segment['text'],
                'segment_start': segment['start'],
                'segment_end': segment['end'],
                'words': []
            }
            
            # Check if we have word-level timestamps
            if 'words' in segment:
                for word_info in segment['words']:
                    word_text = word_info['word'].strip()
                    word_start = word_info['start']
                    word_end = word_info['end']
                    
                    # Convert word to phonemes
                    word_phonemes = phonemize(
                        word_text, 
                        language='en-us', 
                        backend='espeak',
                        strip=True
                    )
                    
                    # Split phonemes (they come as a string like "həˈloʊ")
                    phoneme_list = list(word_phonemes.replace(' ', ''))
                    
                    # Distribute phonemes evenly across word duration
                    word_duration = word_end - word_start
                    phoneme_count = len(phoneme_list)
                    
                    if phoneme_count > 0:
                        phoneme_duration = word_duration / phoneme_count
                        
                        phoneme_timings = []
                        for i, phoneme in enumerate(phoneme_list):
                            phoneme_start = word_start + (i * phoneme_duration)
                            phoneme_end = phoneme_start + phoneme_duration
                            phoneme_timings.append({
                                'phoneme': phoneme,
                                'start': phoneme_start,
                                'end': phoneme_end
                            })
                        
                        segment_data['words'].append({
                            'word': word_text,
                            'word_start': word_start,
                            'word_end': word_end,
                            'phonemes': word_phonemes,
                            'phoneme_timings': phoneme_timings
                        })
            else:
                # No word-level timestamps, just phonemize the whole segment
                segment_phonemes = phonemize(
                    segment['text'], 
                    language='en-us', 
                    backend='espeak',
                    strip=True
                )
                segment_data['segment_phonemes'] = segment_phonemes
            
            phoneme_data.append(segment_data)
        
        return phoneme_data

    def process(self, audio_file):
        """
        Process an audio file: transcribe, align, and phonemize.
        
        Args:
            audio_file (str): Path to audio file
            
        Returns:
            PhonemeResult: Object containing phoneme data and utility methods
        """
        print("\n" + "="*50)
        print("PHONEME ALIGNMENT PIPELINE")
        print("="*50)
        
        print("\nStep 1: Transcribing audio with WhisperX...")
        segments, audio = self._transcribe(audio_file)

        # Reconstruct full transcript
        full_text = " ".join(seg['text'] for seg in segments)
        
        print("\nStep 2: Aligning words with WhisperX...")
        aligned_segments = self._align_words(segments, audio)
        print("✓ Word alignment successful")
        
        print("\nStep 3: Converting words to phonemes and distributing timestamps...")
        phoneme_data = self._phonemize_segments(aligned_segments)
        
        # Create flat list of all phonemes
        all_phonemes = []
        for seg_data in phoneme_data:
            for word_data in seg_data.get('words', []):
                for pt in word_data['phoneme_timings']:
                    all_phonemes.append({
                        'phoneme': pt['phoneme'],
                        'start': pt['start'],
                        'end': pt['end'],
                        'word': word_data['word'],
                        'segment': seg_data['segment_text']
                    })

        print("\nStep 4: Tracking all vowel phonemes...")

        # --- 3.4 Extract vowels only (prep for formant shifting) ---
        
        vowel_phonemes = [
            p for p in all_phonemes
            if p["phoneme"] in IPA_VOWELS
        ]

        

        print(f"✓ Found {len(vowel_phonemes)} vowel phonemes")
        
        print("✓ Processing complete")
        
        return PhonemeResult(phoneme_data, all_phonemes, full_text), vowel_phonemes

class PhonemeResult:
    """
    Container for phoneme alignment results with export and display methods.
    """
    
    def __init__(self, phoneme_data, all_phonemes, full_text=None):
        """
        Initialize PhonemeResult.
        
        Args:
            phoneme_data (list): Structured phoneme data by segment
            all_phonemes (list): Flat list of all phonemes with timestamps
            full_text (str, optional): Full transcript text
        """
        self.phoneme_data = phoneme_data
        self.all_phonemes = all_phonemes
        self.text = full_text
    
    def export_json(self, filepath):
        """
        Export results to JSON file.
        
        Args:
            filepath (str): Output file path
        """
        with open(filepath, 'w') as f:
            json.dump({
                'segments': self.phoneme_data,
                'all_phonemes': self.all_phonemes
            }, f, indent=2)
        
        print(f"✓ Data exported to: {filepath}")
    
    def print_summary(self):
        """Print a summary of results to console."""
        print("\n" + "="*50)
        print("RESULTS")
        print("="*50)
        
        for i, seg_data in enumerate(self.phoneme_data):
            print(f"\nSegment {i+1}: [{seg_data['segment_start']:.2f}s - {seg_data['segment_end']:.2f}s]")
            print(f"Text: {seg_data['segment_text']}")
            print()
            
            if seg_data['words']:
                for word_data in seg_data['words']:
                    print(f"  Word: '{word_data['word']}' [{word_data['word_start']:.3f}s - {word_data['word_end']:.3f}s]")
                    print(f"  Phonemes: {word_data['phonemes']}")
                    print(f"  Phoneme timings:")
                    for pt in word_data['phoneme_timings']:
                        print(f"    {pt['phoneme']:<3} [{pt['start']:.3f}s - {pt['end']:.3f}s]")
                    print()
            else:
                print(f"  Segment phonemes: {seg_data.get('segment_phonemes', 'N/A')}")
                print()
        
        print("="*50)
        print("EXPORT DATA")
        print("="*50)
        print(f"\nTotal phonemes with timestamps: {len(self.all_phonemes)}")
        print("\nFirst 20 phonemes:")
        for i, p in enumerate(self.all_phonemes[:20]):
            print(f"{i+1}. {p['phoneme']:<3} [{p['start']:.3f}s - {p['end']:.3f}s] (word: '{p['word']}')")
        print("\n" + "="*50)