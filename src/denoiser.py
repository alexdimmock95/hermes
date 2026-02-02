"""Simple adapter for DeepFilterNet denoiser with model selection.

Available models:
- DeepFilterNet: Original (PESQ: 2.81)
- DeepFilterNet2: Faster, embedded-friendly (PESQ: 3.08)
- DeepFilterNet3: Best quality (PESQ: 3.17) - DEFAULT
"""

import numpy as np
import torch
from df.enhance import init_df, enhance

class Denoiser:
    def __init__(self, model_name="DeepFilterNet3", post_filter=False):
        """
        Initialize DeepFilterNet denoiser.
        
        Args:
            model_name: Model to use - "DeepFilterNet", "DeepFilterNet2", or "DeepFilterNet3"
            post_filter: Enable post-filter for extra noise suppression (can be aggressive)
        """
        print(f"Loading {model_name}...")
        self.model_name = model_name
        self.post_filter = post_filter
        
        # Initialize model
        self.model, self.df_state, _ = init_df(
            model_base_dir=model_name,
            post_filter=post_filter
        )
        
        print(f"✓ {model_name} denoiser initialized")
        if post_filter:
            print("  Post-filter: ENABLED (more aggressive)")
        else:
            print("  Post-filter: DISABLED (preserves more audio)")
        
    def process_audio(self, frame: np.ndarray) -> np.ndarray:
        """
        Process a single audio frame (1D numpy array).
        
        Args:
            frame: 1D numpy array of audio samples
            
        Returns:
            Denoised audio frame
        """
        # Ensure mono
        if frame.ndim != 1:
            raise ValueError(f"Expected 1D audio, got shape {frame.shape}")
        
        # Add channel dimension [samples] -> [1, samples]
        frame = frame[np.newaxis, :]
        
        # Ensure float32
        frame = frame.astype(np.float32)
        
        # Convert to torch tensor
        frame_tensor = torch.from_numpy(frame)
        
        try:
            # Process through DeepFilterNet
            enhanced_tensor = enhance(self.model, self.df_state, frame_tensor)
            
            # Convert back to numpy
            enhanced = enhanced_tensor.numpy()
            
            # Flatten to 1D
            enhanced = enhanced.flatten()
            
            print(f"[INFO] Denoising succeeded with {self.model_name}")
            
        except Exception as e:
            print(f"Warning: Denoising failed: {e}")
            import traceback
            traceback.print_exc()
            return frame.flatten()
        
        return enhanced