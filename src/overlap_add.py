"""Overlap-add reconstruction for audio frames."""

import numpy as np

def reconstruct_audio(frames, chunk_size, overlap_size):
    """
    Reconstruct audio from overlapping frames using overlap-add.
    
    Args:
        frames: List of audio frames (1D numpy arrays)
        chunk_size: Size of each frame in samples
        overlap_size: Number of overlapping samples between frames
        
    Returns:
        Reconstructed 1D audio array
    """
    if not frames:
        return np.array([])
    
    hop_size = chunk_size - overlap_size
    num_frames = len(frames)
    output_length = (num_frames - 1) * hop_size + chunk_size
    
    final_audio = np.zeros(output_length, dtype=np.float32)
    window = np.hanning(chunk_size).astype(np.float32)
    weight = np.zeros(output_length, dtype=np.float32)
    
    # Overlap-add
    for i, frame in enumerate(frames):
        start = i * hop_size
        end = start + chunk_size
        final_audio[start:end] += frame * window
        weight[start:end] += window
    
    # Normalize
    weight[weight < 1e-8] = 1.0
    final_audio = final_audio / weight
    
    return final_audio