import numpy as np
import librosa
from typing import List, Tuple
from faster_whisper import WhisperModel

class ASRWrapper:
    def __init__(self, model_name='tiny'):
        self.model = WhisperModel(model_name, device="cpu", compute_type="int8")

    def transcribe_full(self, audio: np.ndarray, sr=16000) -> List[Tuple[str, float, float, float]]:
        # Normalise if values look too large
        if np.max(np.abs(audio)) > 1.5:
            audio = audio / np.max(np.abs(audio))

        # Convert to mono if needed
        if audio.ndim == 2:
            audio = audio.mean(axis=1)      
  
        # Resample to 16000 Hz
        if sr != 16000:
            audio = librosa.resample(y=audio, orig_sr=sr, target_sr=16000)

        # Ensure float32
        audio = audio.astype(np.float32)
        
        # Run transcription
        segments, _ = self.model.transcribe(audio, word_timestamps=True)
        words = []
        for segment in segments:
            for word in segment.words:
                words.append((
                    word.word,
                    word.start,
                    word.end,
                    word.probability
                ))
        return words