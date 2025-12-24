import torch

import warnings
import os

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

# Configuration
device = "cpu"
audio_file = "/Users/Alex/Documents/Coding/personal_project/accent_softener/audio_files/input/youtube_noise.wav"
batch_size = 16
compute_type = "int8"

print("="*80)
print("PHONEME ALIGNMENT PIPELINE")
print("="*80)

print("\nStep 1: Transcribing audio with WhisperX...")
model = whisperx.load_model("base", device, compute_type=compute_type, language="en")
audio = whisperx.load_audio(audio_file)
transcription_result = model.transcribe(audio, batch_size=batch_size)

# Handle both dict and list formats
if isinstance(transcription_result, dict):
    initial_segments = transcription_result["segments"]
else:
    initial_segments = transcription_result

print("\nStep 2: Aligning words with WhisperX...")
try:
    model_a, metadata = whisperx.load_align_model(language_code="en", device=device)
    aligned_result = whisperx.align(
        initial_segments, 
        model_a, 
        metadata, 
        audio, 
        device, 
        return_char_alignments=False
    )
    segments = aligned_result["segments"]
    print("✓ Word alignment successful")
except Exception as e:
    print(f"✗ Word alignment failed: {e}")
    print("  Continuing with segment-level timestamps only...")
    segments = initial_segments

print("\nStep 3: Converting words to phonemes and distributing timestamps...")

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

print("\n" + "="*80)
print("RESULTS")
print("="*80)

for i, seg_data in enumerate(phoneme_data):
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

print("="*80)
print("EXPORT DATA")
print("="*80)

# Create a flat list of all phonemes with timestamps for easy export
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

print(f"\nTotal phonemes with timestamps: {len(all_phonemes)}")
print("\nFirst 20 phonemes:")
for i, p in enumerate(all_phonemes[:20]):
    print(f"{i+1}. {p['phoneme']:<3} [{p['start']:.3f}s - {p['end']:.3f}s] (word: '{p['word']}')")

# You can now export this data
import json
output_file = "/Users/Alex/Documents/Coding/personal_project/accent_softener/phoneme_output.json"
with open(output_file, 'w') as f:
    json.dump({
        'segments': phoneme_data,
        'all_phonemes': all_phonemes
    }, f, indent=2)

print(f"\n✓ Data exported to: {output_file}")
print("\n" + "="*80)



'''
#### THE BELOW CODE WORKS WITH GETTING WORD TIMESTAMPS AND SHARES PHONEME ACROSS WORD DURATION

import torch
import os

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

# Configuration
device = "cpu"
audio_file = "/Users/Alex/Documents/Coding/personal_project/accent_softener/audio_files/input/youtube_noise.wav"
batch_size = 16
compute_type = "int8"

print("="*80)
print("PHONEME ALIGNMENT PIPELINE")
print("="*80)

print("\nStep 1: Transcribing audio with WhisperX...")
model = whisperx.load_model("base", device, compute_type=compute_type, language="en")
audio = whisperx.load_audio(audio_file)
transcription_result = model.transcribe(audio, batch_size=batch_size)

# Handle both dict and list formats
if isinstance(transcription_result, dict):
    initial_segments = transcription_result["segments"]
else:
    initial_segments = transcription_result

print("\nStep 2: Aligning words with WhisperX...")
try:
    model_a, metadata = whisperx.load_align_model(language_code="en", device=device)
    aligned_result = whisperx.align(
        initial_segments, 
        model_a, 
        metadata, 
        audio, 
        device, 
        return_char_alignments=False
    )
    segments = aligned_result["segments"]
    print("✓ Word alignment successful")
except Exception as e:
    print(f"✗ Word alignment failed: {e}")
    print("  Continuing with segment-level timestamps only...")
    segments = initial_segments

print("\nStep 3: Converting words to phonemes and distributing timestamps...")

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

print("\n" + "="*80)
print("RESULTS")
print("="*80)

for i, seg_data in enumerate(phoneme_data):
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

print("="*80)
print("EXPORT DATA")
print("="*80)

# Create a flat list of all phonemes with timestamps for easy export
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

print(f"\nTotal phonemes with timestamps: {len(all_phonemes)}")
print("\nFirst 20 phonemes:")
for i, p in enumerate(all_phonemes[:20]):
    print(f"{i+1}. {p['phoneme']:<3} [{p['start']:.3f}s - {p['end']:.3f}s] (word: '{p['word']}')")

# You can now export this data
import json
output_file = "/Users/Alex/Documents/Coding/personal_project/accent_softener/phoneme_output.json"
with open(output_file, 'w') as f:
    json.dump({
        'segments': phoneme_data,
        'all_phonemes': all_phonemes
    }, f, indent=2)

print(f"\n✓ Data exported to: {output_file}")
print("\n" + "="*80)'''