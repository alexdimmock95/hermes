"""
Pronunciation Scoring System with Full Debugging
Version: 2.1 - Fixed Jaccard calculation and improved debug output
"""

import torch
import numpy as np
import librosa
from transformers import Wav2Vec2ForCTC, Wav2Vec2Processor
from scipy.spatial.distance import euclidean
from fastdtw import fastdtw
import io
from typing import Tuple, Dict
import warnings
warnings.filterwarnings('ignore')
import time
from contextlib import contextmanager

import os
# Set espeak path for phonemizer
os.environ['PATH'] = '/opt/homebrew/bin:' + os.environ.get('PATH', '')


@contextmanager
def timer(description: str, debug: bool = False):
    """Context manager for timing code blocks."""
    start = time.time()
    yield
    elapsed = time.time() - start
    if debug:
        print(f"⏱️  {description}: {elapsed:.3f}s ({elapsed*1000:.1f}ms)")


class PronunciationScore:
    """
    Multi-language pronunciation scorer with comprehensive debugging.
    
    Set debug=True to see detailed scoring breakdown.
    """
    
    # Language-specific models
    LANGUAGE_MODELS = {
        'en': "facebook/wav2vec2-base-960h",
        'fr': "facebook/wav2vec2-large-xlsr-53-french",
        'es': "facebook/wav2vec2-large-xlsr-53-spanish",
        'de': "facebook/wav2vec2-large-xlsr-53-german",
        'it': "facebook/wav2vec2-large-xlsr-53-italian",
        'pt': "facebook/wav2vec2-large-xlsr-53-portuguese",
        'ru': "facebook/wav2vec2-large-xlsr-53-russian",
        'pl': "facebook/wav2vec2-large-xlsr-53-polish",
        'ja': "facebook/wav2vec2-large-xlsr-53-japanese",
        'zh-CN': "facebook/wav2vec2-large-xlsr-53-chinese-zh-cn",
        'ar': "facebook/wav2vec2-large-xlsr-53-arabic",
        'tr': "facebook/wav2vec2-large-xlsr-53-turkish",
        'nl': "facebook/wav2vec2-large-xlsr-53-dutch",
    }
    
    # Espeak language codes
    ESPEAK_LANGUAGES = {
        'en': 'en-us',
        'fr': 'fr-fr',
        'es': 'es',
        'de': 'de',
        'it': 'it',
        'pt': 'pt',
        'ru': 'ru',
        'pl': 'pl',
        'ja': 'ja',
        'zh-CN': 'zh',
        'ar': 'ar',
        'tr': 'tr',
        'nl': 'nl',
    }
    
    def __init__(self, language: str = "en", debug: bool = False):
        """
        Initialize scorer for a specific language.
        
        Args:
            language: Language code (e.g., 'en', 'fr', 'es')
            debug: Enable detailed debugging output
        """
        self.debug = debug
        self.language = language
        
        if self.debug:
            print(f"Initializing pronunciation scorer for {language.upper()} with DEBUG mode enabled...")
            start_time = time.time()
        else:
            print(f"Loading pronunciation scoring models for {language.upper()}...")
        
        # Get language-specific model or fallback to English
        model_name = self.LANGUAGE_MODELS.get(language, self.LANGUAGE_MODELS['en'])
        
        if language not in self.LANGUAGE_MODELS:
            print(f"⚠️  No specific model for '{language}', using multilingual fallback")
            model_name = "facebook/wav2vec2-large-xlsr-53-multilingual"
        
        with timer(f"Loading processor for {model_name}", self.debug):
            self.processor = Wav2Vec2Processor.from_pretrained(model_name)
        
        with timer(f"Loading model for {model_name}", self.debug):
            self.model = Wav2Vec2ForCTC.from_pretrained(model_name)
            self.model.eval()
        
        self.sample_rate = 16000
        self.n_mfcc = 13
        self.n_fft = 400
        self.hop_length = 160
        
        if self.debug:
            total_time = time.time() - start_time
            print(f"✓ Models loaded successfully for {language.upper()} in {total_time:.2f}s")
        else:
            print(f"✓ Models loaded successfully for {language.upper()}")
    
    def load_audio(self, audio_data: bytes) -> np.ndarray:
        """Load and normalize audio."""
        audio_io = io.BytesIO(audio_data)
        audio, sr = librosa.load(audio_io, sr=self.sample_rate)
        
        # Normalize amplitude
        if len(audio) > 0:
            max_amp = np.max(np.abs(audio))
            if max_amp > 0:
                audio = audio / max_amp
        
        return audio
    
    def extract_mfcc(self, audio: np.ndarray) -> np.ndarray:
        """Extract MFCCs with optional debugging."""
        # Add tiny noise to prevent numerical issues
        audio = audio + np.random.normal(0, 1e-6, len(audio))
        
        mfcc = librosa.feature.mfcc(
            y=audio,
            sr=self.sample_rate,
            n_mfcc=self.n_mfcc,
            n_fft=self.n_fft,
            hop_length=self.hop_length
        )
        
        # Normalize
        mfcc = (mfcc - np.mean(mfcc, axis=1, keepdims=True)) / (
            np.std(mfcc, axis=1, keepdims=True) + 1e-8
        )
        
        return mfcc
    
    def compute_dtw_distance(
        self, 
        mfcc_user: np.ndarray, 
        mfcc_ref: np.ndarray
    ) -> Tuple[float, np.ndarray]:
        """Compute DTW distance with improved normalization."""
        user_seq = mfcc_user.T
        ref_seq = mfcc_ref.T
        
        distance, path = fastdtw(user_seq, ref_seq, dist=euclidean)
        
        # Improved normalization
        normalized_distance = distance / np.sqrt(len(path))
        
        return normalized_distance, np.array(path)
    
    def recognize_phonemes(self, audio: np.ndarray) -> Dict[str, any]:
        """Recognize speech using Wav2Vec2."""
        # Handle audio length
        target_length = self.sample_rate * 5
        if len(audio) > target_length:
            audio = audio[:target_length]
        elif len(audio) < self.sample_rate * 0.3:
            audio = np.pad(audio, (0, int(self.sample_rate * 0.3) - len(audio)))
        
        input_values = self.processor(
            audio, 
            sampling_rate=self.sample_rate, 
            return_tensors="pt"
        ).input_values
        
        with torch.no_grad():
            logits = self.model(input_values).logits
        
        predicted_ids = torch.argmax(logits, dim=-1)
        transcription = self.processor.batch_decode(predicted_ids)[0]
        
        probs = torch.nn.functional.softmax(logits, dim=-1)
        max_probs = torch.max(probs, dim=-1).values
        confidence = torch.mean(max_probs).item()
        
        return {
            "text": transcription.lower().strip(),
            "confidence": confidence
        }
    

    def score_pronunciation(self, user_audio_bytes: bytes, reference_audio_bytes: bytes, target_word: str) -> Dict[str, any]:
        """
        Score pronunciation with detailed debugging and performance metrics.
        """
        # Initialize metrics dictionary
        metrics = {
            "total_time": 0,
            "audio_loading_time": 0,
            "mfcc_extraction_time": 0,
            "dtw_computation_time": 0,
            "speech_recognition_time": 0,
            "phoneme_analysis_time": 0,
        }
        
        overall_start = time.time()
        
        if self.debug:
            print("\n" + "="*70)
            print("PRONUNCIATION SCORING - DEBUG MODE")
            print("="*70)
            print(f"Target word: '{target_word}'")
            print(f"Language: {self.language.upper()}")
        
        # Load audio
        with timer("Audio loading", self.debug):
            load_start = time.time()
            user_audio = self.load_audio(user_audio_bytes)
            ref_audio = self.load_audio(reference_audio_bytes)
            metrics["audio_loading_time"] = time.time() - load_start
        
        if self.debug:
            print(f"\n📊 AUDIO STATISTICS")
            print(f"├─ User audio:")
            print(f"│  ├─ Length: {len(user_audio)} samples ({len(user_audio)/self.sample_rate:.2f}s)")
            print(f"│  ├─ Amplitude: min={user_audio.min():.3f}, max={user_audio.max():.3f}")
            print(f"│  └─ Energy: {np.sum(user_audio**2):.3f}")
            print(f"└─ Reference audio:")
            print(f"   ├─ Length: {len(ref_audio)} samples ({len(ref_audio)/self.sample_rate:.2f}s)")
            print(f"   ├─ Amplitude: min={ref_audio.min():.3f}, max={ref_audio.max():.3f}")
            print(f"   └─ Energy: {np.sum(ref_audio**2):.3f}")
        
        # Extract MFCCs
        with timer("MFCC extraction", self.debug):
            mfcc_start = time.time()
            user_mfcc = self.extract_mfcc(user_audio)
            ref_mfcc = self.extract_mfcc(ref_audio)
            metrics["mfcc_extraction_time"] = time.time() - mfcc_start
        
        if self.debug:
            print(f"\n📈 MFCC FEATURES")
            print(f"├─ User MFCCs: shape {user_mfcc.shape} ({user_mfcc.shape[1]} frames)")
            print(f"│  ├─ Mean: {user_mfcc.mean():.4f}")
            print(f"│  ├─ Std: {user_mfcc.std():.4f}")
            print(f"│  └─ First 3 coefficients (frame 0): {user_mfcc[:3, 0]}")
            print(f"└─ Reference MFCCs: shape {ref_mfcc.shape} ({ref_mfcc.shape[1]} frames)")
            print(f"   ├─ Mean: {ref_mfcc.mean():.4f}")
            print(f"   ├─ Std: {ref_mfcc.std():.4f}")
            print(f"   └─ First 3 coefficients (frame 0): {ref_mfcc[:3, 0]}")
        
        # Compute DTW
        with timer("DTW computation", self.debug):
            dtw_start = time.time()
            dtw_distance, alignment_path = self.compute_dtw_distance(user_mfcc, ref_mfcc)
            metrics["dtw_computation_time"] = time.time() - dtw_start
        
        if self.debug:
            print(f"\n🔄 DYNAMIC TIME WARPING")
            print(f"├─ Raw DTW distance: {dtw_distance:.4f}")
            print(f"├─ Alignment path length: {len(alignment_path)}")
            print(f"├─ Interpretation:")
            if dtw_distance < 2.0:
                print(f"│  └─ ⭐ EXCELLENT - Near-perfect acoustic match")
            elif dtw_distance < 3.5:
                print(f"│  └─ ✅ VERY GOOD - Strong acoustic similarity")
            elif dtw_distance < 5.0:
                print(f"│  └─ 👍 GOOD - Acceptable acoustic match")
            elif dtw_distance < 6.5:
                print(f"│  └─ 👌 FAIR - Some acoustic differences")
            else:
                print(f"│  └─ ⚠️  POOR - Significant acoustic differences")
            print(f"└─ Expected ranges:")
            print(f"   ├─ Perfect (TTS vs TTS): 0.5-1.5")
            print(f"   ├─ Excellent (native): 1.5-3.0")
            print(f"   ├─ Good (clear): 3.0-5.0")
            print(f"   └─ Fair (accent): 5.0-7.0")
        
        # Speech recognition
        with timer("Speech recognition (Wav2Vec2)", self.debug):
            recog_start = time.time()
            user_recognition = self.recognize_phonemes(user_audio)
            ref_recognition = self.recognize_phonemes(ref_audio)
            metrics["speech_recognition_time"] = time.time() - recog_start
        
        user_text = user_recognition["text"]
        ref_text = ref_recognition["text"]
        target_word_clean = target_word.lower().strip()
        
        if self.debug:
            print(f"\n🎤 SPEECH RECOGNITION (Wav2Vec2)")
            print(f"├─ Target word: '{target_word_clean}'")
            print(f"├─ Reference TTS recognized as: '{ref_text}'")
            print(f"│  └─ Confidence: {ref_recognition['confidence']:.3f}")
            print(f"└─ User audio recognized as: '{user_text}'")
            print(f"   └─ Confidence: {user_recognition['confidence']:.3f}")
            
            if ref_text != target_word_clean:
                print(f"\n⚠️  WARNING: Reference TTS not perfectly recognized!")
                print(f"   Expected: '{target_word_clean}'")
                print(f"   Got:      '{ref_text}'")
                print(f"   This may affect scoring accuracy.")
        
        # Phoneme similarity
        phoneme_match = self._calculate_phoneme_similarity(
            user_text, 
            target_word_clean
        )
        
        if self.debug:
            print(f"\n🔤 PHONEME SIMILARITY ANALYSIS")
            print(f"├─ Comparing: '{user_text}' vs '{target_word_clean}'")
            print(f"├─ Overall similarity: {phoneme_match:.3f}")
            
            # Character comparison
            max_len = max(len(user_text), len(target_word_clean))
            if max_len <= 20:  # Only show for short words
                print(f"├─ Character-by-character:")
                user_padded = user_text.ljust(max_len)
                target_padded = target_word_clean.ljust(max_len)
                
                for i, (u, t) in enumerate(zip(user_padded, target_padded)):
                    match = "✓" if u == t else "✗"
                    if u == ' ' and t == ' ':
                        continue
                    u_display = u if u != ' ' else '_'
                    t_display = t if t != ' ' else '_'
                    print(f"│  [{i}] '{u_display}' vs '{t_display}' {match}")
            
            # Detailed metrics
            edit_dist = self._levenshtein_distance(user_text, target_word_clean)
            set_user = set(user_text.replace(" ", ""))
            set_target = set(target_word_clean.replace(" ", ""))
            
            intersection = set_user & set_target
            union = set_user | set_target
            jaccard = len(intersection) / len(union) if len(union) > 0 else 0.0
            
            len_ratio = (
                min(len(user_text), len(target_word_clean)) / 
                max(len(user_text), len(target_word_clean), 1)
            )
            
            print(f"├─ Edit (Levenshtein) distance: {edit_dist}")
            print(f"├─ Jaccard similarity: {jaccard:.3f}")
            print(f"└─ Length ratio: {len_ratio:.3f}")
        
        # Calculate scores
        is_perfect_match = (user_text == target_word_clean)
        is_near_perfect = (phoneme_match >= 0.95)

        if is_perfect_match or is_near_perfect:
            if dtw_distance < 4.0:
                dtw_score = 95
            elif dtw_distance < 6.0:
                dtw_score = 88
            elif dtw_distance < 8.0:
                dtw_score = 80
            else:
                dtw_score = 72
            
            if self.debug:
                print(f"\n⭐ PERFECT/NEAR-PERFECT MATCH - Lenient acoustic scoring applied")
        else:
            if dtw_distance < 3.0:
                dtw_score = 100
            elif dtw_distance < 5.5:
                dtw_score = 100 - ((dtw_distance - 3.0) * 10)
            elif dtw_distance < 8.0:
                dtw_score = 75 - ((dtw_distance - 5.5) * 12)
            else:
                dtw_score = max(40, 45 - ((dtw_distance - 8.0) * 3))

        dtw_score = max(0, min(100, dtw_score))
        phoneme_score = phoneme_match * 100
        
        # Dynamic weighting
        if phoneme_match > 0.8:
            overall_score = (dtw_score * 0.4) + (phoneme_score * 0.6)
            weights = "40% DTW + 60% Phoneme (high confidence)"
        else:
            overall_score = (dtw_score * 0.5) + (phoneme_score * 0.5)
            weights = "50% DTW + 50% Phoneme (balanced)"
        
        overall_score = max(0, min(100, overall_score))
        
        if self.debug:
            print(f"\n📊 SCORE CALCULATION")
            print(f"├─ DTW Score: {dtw_score:.1f}/100")
            print(f"│  └─ Based on distance {dtw_distance:.3f}")
            print(f"├─ Phoneme Score: {phoneme_score:.1f}/100")
            print(f"│  └─ Based on similarity {phoneme_match:.3f}")
            print(f"├─ Weighting: {weights}")
            print(f"└─ OVERALL SCORE: {overall_score:.1f}/100")
            
            # Grade interpretation
            if overall_score >= 90:
                grade = "A (Excellent)"
            elif overall_score >= 80:
                grade = "B (Very Good)"
            elif overall_score >= 70:
                grade = "C (Good)"
            elif overall_score >= 60:
                grade = "D (Fair)"
            else:
                grade = "F (Needs Practice)"
            print(f"   └─ Grade: {grade}")
        
        # Phoneme-level analysis
        phoneme_analysis = None
        try:
            with timer("Phoneme analysis (IPA extraction)", self.debug):
                phoneme_start = time.time()
                phoneme_analysis = self._analyze_phoneme_differences(
                    user_text,
                    target_word_clean,
                    user_audio,
                    ref_audio
                )
                metrics["phoneme_analysis_time"] = time.time() - phoneme_start

            if self.debug and phoneme_analysis:
                print(f"\n📝 PHONEME FEEDBACK:")
                print(phoneme_analysis['feedback'])
        except Exception as e:
            if self.debug:
                print(f"\n⚠️  Could not perform phoneme analysis: {e}")
                print(f"   Make sure phonemizer is installed: pip install phonemizer")

        # Generate feedback
        feedback = self._generate_feedback(
            overall_score, dtw_score, phoneme_score,
            user_text, target_word_clean, dtw_distance
        )
        
        # Calculate total time
        metrics["total_time"] = time.time() - overall_start
        
        if self.debug:
            print(f"\n⏱️  PERFORMANCE METRICS")
            print(f"├─ Audio loading: {metrics['audio_loading_time']*1000:.1f}ms")
            print(f"├─ MFCC extraction: {metrics['mfcc_extraction_time']*1000:.1f}ms")
            print(f"├─ DTW computation: {metrics['dtw_computation_time']*1000:.1f}ms")
            print(f"├─ Speech recognition: {metrics['speech_recognition_time']*1000:.1f}ms")
            print(f"├─ Phoneme analysis: {metrics['phoneme_analysis_time']*1000:.1f}ms")
            print(f"└─ TOTAL TIME: {metrics['total_time']:.3f}s")
            
            # Calculate percentages
            if metrics["total_time"] > 0:
                print(f"\n📊 TIME BREAKDOWN")
                for key, value in metrics.items():
                    if key != "total_time" and value > 0:
                        percentage = (value / metrics["total_time"]) * 100
                        label = key.replace("_", " ").title()
                        print(f"   {label}: {percentage:.1f}%")
            
            print("="*70 + "\n")
            
        return {
            "overall_score": round(overall_score, 1),
            "dtw_score": round(dtw_score, 1),
            "phoneme_score": round(phoneme_score, 1),
            "recognized_text": user_text,
            "target_word": target_word_clean,
            "reference_text": ref_text,
            "dtw_distance": round(dtw_distance, 3),
            "alignment_quality": len(alignment_path),
            "feedback": feedback,
            "phoneme_analysis": phoneme_analysis,
            "metrics": metrics if self.debug else None,  # Include metrics in response
            "debug_info": {
                "user_confidence": user_recognition["confidence"],
                "ref_confidence": ref_recognition["confidence"],
                "phoneme_match": phoneme_match,
                "weights_used": weights,
                "user_audio_length": len(user_audio) / self.sample_rate,
                "ref_audio_length": len(ref_audio) / self.sample_rate
            } if self.debug else None
        }


    def _calculate_phoneme_similarity(self, recognized: str, target: str) -> float:
        """Calculate phoneme similarity."""
        recognized = recognized.replace(" ", "").lower()
        target = target.replace(" ", "").lower()
        
        if recognized == target:
            return 1.0
        
        if target in recognized:
            return 0.95
        
        if recognized in target:
            return 0.90
        
        # Jaccard
        set_recognized = set(recognized)
        set_target = set(target)
        
        intersection = set_recognized & set_target
        union = set_recognized | set_target
        
        if len(union) > 0:
            jaccard = len(intersection) / len(union)
        else:
            jaccard = 0.0
        
        # Levenshtein
        edit_distance = self._levenshtein_distance(recognized, target)
        max_len = max(len(recognized), len(target))
        
        if max_len > 0:
            levenshtein_similarity = 1 - (edit_distance / max_len)
        else:
            levenshtein_similarity = 0.0
        
        # Length ratio
        if max(len(recognized), len(target)) > 0:
            len_ratio = min(len(recognized), len(target)) / max(len(recognized), len(target))
        else:
            len_ratio = 0.0
        
        # Weighted combination
        similarity = (
            jaccard * 0.3 +
            levenshtein_similarity * 0.5 +
            len_ratio * 0.2
        )
        
        return max(0.0, min(1.0, similarity))
    
    def _levenshtein_distance(self, s1: str, s2: str) -> int:
        """Calculate edit distance."""
        if len(s1) < len(s2):
            return self._levenshtein_distance(s2, s1)
        
        if len(s2) == 0:
            return len(s1)
        
        previous_row = range(len(s2) + 1)
        
        for i, c1 in enumerate(s1):
            current_row = [i + 1]
            for j, c2 in enumerate(s2):
                insertions = previous_row[j + 1] + 1
                deletions = current_row[j] + 1
                substitutions = previous_row[j] + (c1 != c2)
                current_row.append(min(insertions, deletions, substitutions))
            previous_row = current_row
        
        return previous_row[-1]
    
    def _generate_feedback(
        self, 
        overall: float, 
        dtw: float, 
        phoneme: float,
        recognized: str,
        target: str,
        dtw_distance: float
    ) -> str:
        """Generate encouraging feedback."""
        feedback_parts = []
        
        # Overall assessment
        if overall >= 90:
            feedback_parts.append("🌟 Excellent pronunciation!")
        elif overall >= 80:
            feedback_parts.append("✅ Very good pronunciation!")
        elif overall >= 70:
            feedback_parts.append("👍 Good pronunciation!")
        elif overall >= 60:
            feedback_parts.append("👌 Decent - keep practicing!")
        elif overall >= 50:
            feedback_parts.append("⚠️ Fair - room for improvement.")
        else:
            feedback_parts.append("💪 Keep practicing!")
        
        # Recognition feedback
        recognized_clean = recognized.replace(" ", "")
        target_clean = target.replace(" ", "")
        
        if recognized_clean != target_clean and phoneme < 80:
            if recognized:
                feedback_parts.append(f"Heard: '{recognized}' (expected: '{target}')")
            else:
                feedback_parts.append("Try speaking more clearly.")
        
        # Specific guidance
        if dtw < 70 and phoneme < 70:
            feedback_parts.append("Focus on clarity and rhythm.")
        elif dtw < 70:
            feedback_parts.append("Work on timing and rhythm.")
        elif phoneme < 70:
            feedback_parts.append("Focus on pronouncing each sound.")
        
        if dtw_distance > 6.0:
            feedback_parts.append("Try speaking at a natural pace.")
        
        return " ".join(feedback_parts)


    def _analyze_phoneme_differences(
        self, 
        user_text: str, 
        target_text: str,
        user_audio: np.ndarray,
        ref_audio: np.ndarray
    ) -> Dict[str, any]:
        """
        Analyze which specific phonemes were mispronounced using the target language.
        """
        try:
            if self.debug:
                print(f"\n🔍 ATTEMPTING PHONEME ANALYSIS FOR {self.language.upper()}...")
                print(f"   User text: '{user_text}'")
                print(f"   Target text: '{target_text}'")

            import subprocess
            import shlex

            espeak_path = '/opt/homebrew/bin/espeak-ng'

            if not os.path.exists(espeak_path):
                if self.debug:
                    print(f"   ⚠️  espeak-ng not found at {espeak_path}")
                return None

            if self.debug:
                print(f"   ✓ Found espeak-ng at {espeak_path}")

            espeak_lang = self.ESPEAK_LANGUAGES.get(self.language, 'en-us')

            if self.debug:
                print(f"   ✓ Using espeak voice: {espeak_lang}")

            def get_ipa(text: str) -> str:
                cmd = f'{espeak_path} -q --ipa -v {espeak_lang} "{text}"'
                result = subprocess.run(
                    shlex.split(cmd),
                    capture_output=True,
                    text=True,
                    check=True
                )
                return result.stdout.strip()

            user_phonemes = get_ipa(user_text)
            target_phonemes = get_ipa(target_text)

            if self.debug:
                print(f"   ✓ User IPA: /{user_phonemes}/")
                print(f"   ✓ Target IPA: /{target_phonemes}/")

            mismatches = self._find_phoneme_mismatches(
                user_phonemes,
                target_phonemes
            )

            feedback = self._generate_phoneme_feedback(mismatches)

            return {
                "user_ipa": user_phonemes,
                "target_ipa": target_phonemes,
                "mismatches": mismatches,
                "feedback": feedback
            }

        except subprocess.CalledProcessError as e:
            if self.debug:
                print(f"\n⚠️  espeak-ng subprocess error: {e}")
                print(f"   stdout: {e.stdout}")
                print(f"   stderr: {e.stderr}")
            return None

        except Exception as e:
            if self.debug:
                print(f"\n⚠️  Phoneme analysis error: {type(e).__name__}: {e}")
            return None

                
    def _find_phoneme_mismatches(
        self, 
        user_ipa: str, 
        target_ipa: str
    ) -> list:
        """
        Find which phonemes don't match using alignment.
        
        Returns list of (position, expected_phoneme, actual_phoneme, issue_type)
        """
        mismatches = []
        
        # Simple character-level alignment for IPA
        # (You could make this more sophisticated with DTW on phoneme level)
        user_phones = list(user_ipa.replace(" ", ""))
        target_phones = list(target_ipa.replace(" ", ""))
        
        # Use dynamic programming to align
        m, n = len(user_phones), len(target_phones)
        dp = [[0] * (n + 1) for _ in range(m + 1)]
        
        # Fill DP table
        for i in range(m + 1):
            dp[i][0] = i
        for j in range(n + 1):
            dp[0][j] = j
        
        for i in range(1, m + 1):
            for j in range(1, n + 1):
                if user_phones[i-1] == target_phones[j-1]:
                    dp[i][j] = dp[i-1][j-1]
                else:
                    dp[i][j] = 1 + min(
                        dp[i-1][j],    # deletion
                        dp[i][j-1],    # insertion
                        dp[i-1][j-1]   # substitution
                    )
        
        # Backtrack to find mismatches
        i, j = m, n
        while i > 0 or j > 0:
            if i > 0 and j > 0 and user_phones[i-1] == target_phones[j-1]:
                i -= 1
                j -= 1
            elif i > 0 and j > 0 and dp[i][j] == dp[i-1][j-1] + 1:
                # Substitution (mispronunciation)
                mismatches.append({
                    "position": j,
                    "expected": target_phones[j-1],
                    "actual": user_phones[i-1],
                    "type": "substitution"
                })
                i -= 1
                j -= 1
            elif j > 0 and dp[i][j] == dp[i][j-1] + 1:
                # Insertion (missing sound)
                mismatches.append({
                    "position": j,
                    "expected": target_phones[j-1],
                    "actual": None,
                    "type": "omission"
                })
                j -= 1
            else:
                # Deletion (extra sound)
                mismatches.append({
                    "position": i,
                    "expected": None,
                    "actual": user_phones[i-1],
                    "type": "insertion"
                })
                i -= 1
        
        return list(reversed(mismatches))

    def _generate_phoneme_feedback(self, mismatches: list) -> str:
        """
        Generate human-readable feedback about phoneme errors.
        
        Includes specific articulation tips for common issues.
        """
        if not mismatches:
            return "All sounds pronounced correctly! 🎉"
        
        # Phoneme articulation tips
        ARTICULATION_TIPS = {
            'θ': "TH (voiceless): Place tongue between teeth, blow air (think, bath)",
            'ð': "TH (voiced): Place tongue between teeth, vibrate vocal cords (this, mother)",
            't': "T: Touch tongue tip to alveolar ridge (roof of mouth behind teeth), not behind teeth like Spanish 't'",
            'd': "D: Touch tongue tip to alveolar ridge with voice, not dental like Spanish 'd'",
            'r': "R: Curl tongue back slightly, don't trill or tap like Spanish 'r'",
            'v': "V: Upper teeth touch lower lip, vibrate vocal cords (not 'b')",
            'w': "W: Round lips, don't use 'v' sound like some Spanish speakers",
            'h': "H: Breathe out from throat, like Spanish 'j' but softer",
            'ʃ': "SH: Lips forward, tongue near roof of mouth (ship, wish)",
            'ʒ': "ZH: Like SH but with voice (measure, vision)",
            'tʃ': "CH: Combine T + SH quickly (church, watch)",
            'dʒ': "J: Combine D + ZH quickly (judge, age)",
            'ŋ': "NG: Back of tongue to soft palate (sing, running)",
        }
        
        feedback_parts = []
        
        # Group mismatches by type
        substitutions = [m for m in mismatches if m["type"] == "substitution"]
        omissions = [m for m in mismatches if m["type"] == "omission"]
        insertions = [m for m in mismatches if m["type"] == "insertion"]
        
        if substitutions:
            feedback_parts.append(f"**{len(substitutions)} sound(s) need adjustment:**")
            for mismatch in substitutions[:3]:  # Show max 3
                expected = mismatch["expected"]
                actual = mismatch["actual"]
                tip = ARTICULATION_TIPS.get(expected, "")
                
                if tip:
                    feedback_parts.append(f"  • /{expected}/ (you said /{actual}/): {tip}")
                else:
                    feedback_parts.append(f"  • Expected /{expected}/, heard /{actual}/")
        
        if omissions:
            feedback_parts.append(f"**{len(omissions)} sound(s) were skipped:**")
            for mismatch in omissions[:2]:
                expected = mismatch["expected"]
                tip = ARTICULATION_TIPS.get(expected, "")
                if tip:
                    feedback_parts.append(f"  • Missing /{expected}/: {tip}")
                else:
                    feedback_parts.append(f"  • Don't forget the /{expected}/ sound")
        
        if insertions:
            feedback_parts.append(f"**{len(insertions)} extra sound(s) added:**")
            for mismatch in insertions[:2]:
                actual = mismatch["actual"]
                feedback_parts.append(f"  • Remove the extra /{actual}/ sound")
        
        return "\n".join(feedback_parts)    


def score_user_pronunciation(
    user_recording: bytes,
    target_word: str,
    language: str = 'en',
    scorer: PronunciationScore = None,
    debug: bool = True
) -> Dict[str, any]:
    """
    Score pronunciation with language-specific models.
    
    Args:
        user_recording: User's audio as bytes
        target_word: Word to pronounce
        language: Target language code (e.g., 'en', 'fr', 'es')
        scorer: Existing scorer (optional, must match language)
        debug: Enable debugging output
    """
    # Create new scorer if none provided or language mismatch
    if scorer is None or scorer.language != language:
        scorer = PronunciationScore(language=language, debug=debug)
    elif debug and not scorer.debug:
        scorer.debug = True
    
    # Generate reference with correct language
    from gtts import gTTS
    
    if debug:
        print(f"\n🔊 Generating reference audio for '{target_word}' in {language.upper()} using Google TTS...")
    
    tts = gTTS(text=target_word, lang=language, slow=False)
    ref_audio_buffer = io.BytesIO()
    tts.write_to_fp(ref_audio_buffer)
    ref_audio_bytes = ref_audio_buffer.getvalue()
    
    # Score
    result = scorer.score_pronunciation(
        user_recording,
        ref_audio_bytes,
        target_word
    )
    
    return result

if __name__ == "__main__":
    print("=" * 70)
    print("PRONUNCIATION SCORER v2.1 - FIXED VERSION")
    print("=" * 70)
    
    # Test with debug enabled
    scorer = PronunciationScore(debug=True)
    
    print("\n✓ Scorer initialized")
    print("\nChanges in v2.1:")
    print("  • Fixed Jaccard similarity calculation")
    print("  • Fixed division by zero errors")
    print("  • Improved debug output formatting")
    print("\nTo use debug mode in your bot:")
    print("  result = score_user_pronunciation(audio, word, debug=True)")