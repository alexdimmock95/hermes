# Import necessary libraries
import numpy as np
import soundfile as sf
import librosa

# Define FileStreamer class
# This class reads audio files and yields overlapping frames
# of specified length and overlap.
class FileStreamer:
    def __init__(self, path, sr=16000, chunk_ms=160, overlap_ms=40):
        self.path = path
        self.sr = sr
        self.chunk = int(sr * chunk_ms / 1000) # Chunk size in samples
        self.overlap = int(sr * overlap_ms / 1000) # Overlap size in samples
        self._buffer = None

    def frames(self):
        wav, orig_sr = sf.read(self.path)
        # Ensure mono, 16000Hz sampling rate
        if len(wav.shape) > 1:
            wav = librosa.to_mono(wav.T)
        if orig_sr != self.sr:
            wav = librosa.resample(y=wav, orig_sr = orig_sr, target_sr = self.sr)

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