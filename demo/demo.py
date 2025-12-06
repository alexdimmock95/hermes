# Import necessary libraries
import sys
import numpy as np
import soundfile as sf
from pathlib import Path
sys.path.append(str(Path(__file__).parent.parent))  # add project root
from src.input_streamer import FileStreamer

input_file = Path("/Users/Alex/Documents/Coding/personal_project/accent_softener/audio_files/input/sat_plans.wav")

output_folder = Path("/Users/Alex/Documents/Coding/personal_project/accent_softener/audio_files/output")
output_file = output_folder / f"{input_file.stem}_final{input_file.suffix}"

streamer = FileStreamer(input_file)

output_frames = []

for frame, seq in streamer.frames():
    output_frames.append(frame)

final_audio = np.concatenate(output_frames)
sf.write(output_file, final_audio, samplerate=streamer.sr)