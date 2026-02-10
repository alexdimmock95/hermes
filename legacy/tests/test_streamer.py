import sys
import numpy as np
import soundfile as sf
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))  # add project root
from legacy.src.input_streamer import FileStreamer

def test_chunk_sizes(tmp_path):
    # generate fake audio
    sr = 16000
    audio = np.random.randn(sr)  # 1 second
    wav_path = tmp_path / "test.wav"
    sf.write(wav_path, audio, sr)

    # create streamer
    streamer = FileStreamer(str(wav_path), sr=sr, chunk_ms=160, overlap_ms=40)
    
    # collect frames
    frames = list(streamer.frames())

    # check chunk sizes
    chunk_len = int(sr * 0.160)
    
    # each frame should have the correct length
    for frame, seq in frames:
        assert frame.shape[0] == chunk_len