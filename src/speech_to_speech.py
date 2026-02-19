import whisperx
import librosa
import tempfile
from TTS.api import TTS
from deep_translator import GoogleTranslator
import time
from contextlib import contextmanager
from typing import Dict, Optional

@contextmanager
def timer(description: str, verbose: bool = True):
    """Context manager for timing code blocks."""
    start = time.time()
    yield
    elapsed = time.time() - start
    if verbose:
        print(f"⏱️  {description}: {elapsed:.3f}s ({elapsed*1000:.1f}ms)")

class SpeechToSpeechTranslator:
    """
    Speech-to-speech translation with voice cloning.
    Transcribes audio, translates text, and synthesizes in target language.
    """
    
    def __init__(self, device="cpu", model_size="base", compute_type="int8", batch_size=16, debug=False):
        """
        Initialize translator.
        
        Args:
            device: "cpu" or "cuda"
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            compute_type: Compute type for model ("int8", "float16", "float32")
            batch_size: Batch size for transcription
            debug: Enable detailed performance metrics
        """
        self.device = device
        self.model_size = model_size
        self.compute_type = compute_type
        self.batch_size = batch_size
        self.debug = debug
        
        # Models (initialized as None, loaded later)
        self.model = None  # Whisper model
        self.tts = None    # TTS model

        # Placeholders for transcriptions and languages
        self.source_text = ""
        self.target_text = ""
        self.source_language = ""
        self.target_language = ""
        
        # Performance metrics
        self.last_metrics = {}
    
    def _load_whisper(self):
        """Load Whisper model (lazy loading)"""
        if self.model is None:
            with timer(f"Loading Whisper {self.model_size} model on {self.device}", self.debug):
                self.model = whisperx.load_model(
                    self.model_size,
                    self.device,
                    compute_type=self.compute_type
                )
    
    def _load_tts(self):
        """Load TTS model (lazy loading)"""
        if self.tts is None:
            with timer("Loading TTS model (XTTS v2)", self.debug):
                self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    
    def transcribe(self, audio_path, return_metrics=False):
        """
        Transcribe audio to text using WhisperX.
        
        Args:
            audio_path: Path to audio file
            return_metrics: Whether to return timing metrics
            
        Returns:
            str: Transcribed text
            dict (optional): Metrics if return_metrics=True
        """
        metrics = {
            "model_loading_time": 0,
            "audio_loading_time": 0,
            "transcription_time": 0,
            "total_time": 0
        }
        
        start_total = time.time()
        
        # Load model
        load_start = time.time()
        self._load_whisper()
        metrics["model_loading_time"] = time.time() - load_start
        
        # Load audio
        with timer("Loading audio", self.debug):
            audio_start = time.time()
            audio = whisperx.load_audio(audio_path)
            metrics["audio_loading_time"] = time.time() - audio_start
        
        # Transcribe
        with timer("Transcribing with WhisperX", self.debug):
            transcribe_start = time.time()
            transcription_result = self.model.transcribe(audio, self.batch_size)
            metrics["transcription_time"] = time.time() - transcribe_start
        
        # Handle both dict and list formats
        if isinstance(transcription_result, dict):
            segments = transcription_result["segments"]
        else:
            segments = transcription_result
        
        # Combine segment texts into single string
        text = " ".join([seg["text"].strip() for seg in segments])

        # Store transcription and detect language
        self.source_text = text.strip()
        
        # Try to detect language from transcription result
        if isinstance(transcription_result, dict) and "language" in transcription_result:
            self.source_language = transcription_result["language"]
        else:
            # Fallback: assume English if language not detected
            self.source_language = "en"
        
        metrics["total_time"] = time.time() - start_total
        
        if self.debug:
            print(f"\n📊 TRANSCRIPTION METRICS")
            print(f"├─ Model loading: {metrics['model_loading_time']*1000:.1f}ms")
            print(f"├─ Audio loading: {metrics['audio_loading_time']*1000:.1f}ms")
            print(f"├─ Transcription: {metrics['transcription_time']*1000:.1f}ms")
            print(f"└─ Total: {metrics['total_time']:.3f}s")
        
        if return_metrics:
            return text, metrics
        return text
    
    def translate(self, text, target_language="fr", return_metrics=False):
        """
        Translate text to target language.
        
        Args:
            text: Source text
            target_language: Target language code
            return_metrics: Whether to return timing metrics
            
        Returns:
            str: Translated text
            dict (optional): Metrics if return_metrics=True
        """
        metrics = {"translation_time": 0}
        
        with timer(f"Translating to {target_language}", self.debug):
            translate_start = time.time()
            translator = GoogleTranslator(source='auto', target=target_language)
            translated = translator.translate(text)
            metrics["translation_time"] = time.time() - translate_start

        # Store translated text and target language
        self.target_text = translated
        self.target_language = target_language

        if self.debug:
            print(f"\n📊 TRANSLATION METRICS")
            print(f"└─ Translation time: {metrics['translation_time']*1000:.1f}ms")
        
        if return_metrics:
            return translated, metrics
        return translated

    def detect_language(self, text):
        """
        Detect the language of the input text.
        
        Args:
            text: Text to detect language for
            
        Returns:
            str: Language code (e.g., 'en', 'fr', 'es') or None if detection fails
        """
        if not text or not text.strip():
            return None
        
        try:
            with timer("Language detection", self.debug):
                from langdetect import detect
                lang_code = detect(text)
                return lang_code
        except Exception as e:
            print(f"Language detection error: {e}")
            return None

    def get_source_language(self):
        """
        Get the detected source language from the last transcription.
        
        Returns:
            str: Language code or 'en' as default
        """
        return self.source_language if self.source_language else "en"
    
    def synthesize(self, text, speaker_wav, language="fr", return_metrics=False):
        """
        Synthesize speech with voice cloning.
        
        Args:
            text: Text to synthesize
            speaker_wav: Path to reference audio for voice cloning
            language: Target language code
            return_metrics: Whether to return timing metrics
            
        Returns:
            tuple: (audio_array, sample_rate)
            dict (optional): Metrics if return_metrics=True
        """
        metrics = {
            "tts_loading_time": 0,
            "synthesis_time": 0,
            "audio_loading_time": 0,
            "total_time": 0
        }
        
        start_total = time.time()
        
        # Load TTS model
        load_start = time.time()
        self._load_tts()
        metrics["tts_loading_time"] = time.time() - load_start
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            # Synthesize
            with timer("Synthesizing speech with voice cloning", self.debug):
                synth_start = time.time()
                self.tts.tts_to_file(
                    text=text,
                    speaker_wav=speaker_wav,
                    language=language,
                    file_path=tmp.name
                )
                metrics["synthesis_time"] = time.time() - synth_start
            
            # Load synthesized audio
            with timer("Loading synthesized audio", self.debug):
                audio_start = time.time()
                audio, sr = librosa.load(tmp.name, sr=None)
                metrics["audio_loading_time"] = time.time() - audio_start
        
        metrics["total_time"] = time.time() - start_total
        
        if self.debug:
            print(f"\n📊 SYNTHESIS METRICS")
            print(f"├─ TTS loading: {metrics['tts_loading_time']*1000:.1f}ms")
            print(f"├─ Synthesis: {metrics['synthesis_time']:.3f}s")
            print(f"├─ Audio loading: {metrics['audio_loading_time']*1000:.1f}ms")
            print(f"└─ Total: {metrics['total_time']:.3f}s")
        
        if return_metrics:
            return (audio, sr), metrics
        return audio, sr
    
    def translate_speech(self, audio_path, text=None, target_language="fr", return_metrics=False):
        """
        Full pipeline: speech → text → translation → speech.
        
        Args:
            audio_path: Path to input audio
            text: Pre-transcribed text (optional, will transcribe if not provided)
            target_language: Target language code
            return_metrics: Whether to return detailed timing metrics
            
        Returns:
            tuple: (output_audio, sample_rate)
            dict (optional): Comprehensive metrics if return_metrics=True
        """
        overall_start = time.time()
        
        print("\n" + "="*50)
        print("SPEECH-TO-SPEECH TRANSLATION")
        if self.debug:
            print("DEBUG MODE ENABLED")
        print("="*50)
        
        all_metrics = {
            "transcription": {},
            "translation": {},
            "synthesis": {},
            "total_time": 0,
            "pipeline_stages": {}
        }
        
        # Step 1: Transcribe (if needed)
        stage_start = time.time()
        if text is None:
            print("\n[1/3] Transcribing audio...")
            if return_metrics:
                text, transcribe_metrics = self.transcribe(audio_path, return_metrics=True)
                all_metrics["transcription"] = transcribe_metrics
            else:
                text = self.transcribe(audio_path)
            print(f"      Transcribed: '{text}'")
        else:
            print(f"\n[1/3] Using provided text: '{text}'")
            # Store provided text and assume English
            self.source_text = text
            self.source_language = "en"
        
        all_metrics["pipeline_stages"]["transcription"] = time.time() - stage_start
        
        # Step 2: Translate
        stage_start = time.time()
        print(f"\n[2/3] Translating to {target_language}...")
        if return_metrics:
            translated_text, translate_metrics = self.translate(text, target_language, return_metrics=True)
            all_metrics["translation"] = translate_metrics
        else:
            translated_text = self.translate(text, target_language)
        print(f"      Translated: '{translated_text}'")
        
        all_metrics["pipeline_stages"]["translation"] = time.time() - stage_start
        
        # Step 3: Synthesize
        stage_start = time.time()
        print("\n[3/3] Synthesizing with voice cloning...")
        if return_metrics:
            (output_audio, sr), synth_metrics = self.synthesize(
                translated_text, 
                audio_path, 
                target_language,
                return_metrics=True
            )
            all_metrics["synthesis"] = synth_metrics
        else:
            output_audio, sr = self.synthesize(
                translated_text, 
                audio_path, 
                target_language
            )
        print("      ✓ Complete")
        
        all_metrics["pipeline_stages"]["synthesis"] = time.time() - stage_start
        all_metrics["total_time"] = time.time() - overall_start
        
        # Store metrics for later access
        self.last_metrics = all_metrics
        
        if self.debug or return_metrics:
            print(f"\n{'='*50}")
            print("📊 COMPLETE PIPELINE METRICS")
            print(f"{'='*50}")
            print(f"\n⏱️  STAGE BREAKDOWN:")
            print(f"├─ Transcription: {all_metrics['pipeline_stages'].get('transcription', 0):.3f}s")
            print(f"├─ Translation: {all_metrics['pipeline_stages'].get('translation', 0):.3f}s")
            print(f"├─ Synthesis: {all_metrics['pipeline_stages'].get('synthesis', 0):.3f}s")
            print(f"└─ TOTAL PIPELINE: {all_metrics['total_time']:.3f}s")
            
            # Percentage breakdown
            total = all_metrics['total_time']
            if total > 0:
                print(f"\n📊 TIME ALLOCATION:")
                for stage, duration in all_metrics['pipeline_stages'].items():
                    percentage = (duration / total) * 100
                    print(f"   {stage.title()}: {percentage:.1f}%")
            
            # Detailed breakdown if available
            if all_metrics.get("transcription"):
                print(f"\n🎤 TRANSCRIPTION DETAILS:")
                t = all_metrics["transcription"]
                print(f"   Model loading: {t.get('model_loading_time', 0)*1000:.1f}ms")
                print(f"   Audio loading: {t.get('audio_loading_time', 0)*1000:.1f}ms")
                print(f"   Processing: {t.get('transcription_time', 0)*1000:.1f}ms")
            
            if all_metrics.get("translation"):
                print(f"\n🌐 TRANSLATION DETAILS:")
                print(f"   API call: {all_metrics['translation'].get('translation_time', 0)*1000:.1f}ms")
            
            if all_metrics.get("synthesis"):
                print(f"\n🔊 SYNTHESIS DETAILS:")
                s = all_metrics["synthesis"]
                print(f"   Model loading: {s.get('tts_loading_time', 0)*1000:.1f}ms")
                print(f"   Voice cloning: {s.get('synthesis_time', 0):.3f}s")
                print(f"   Audio loading: {s.get('audio_loading_time', 0)*1000:.1f}ms")
            
            print(f"{'='*50}\n")
        
        if return_metrics:
            return (output_audio, sr), all_metrics
        return output_audio, sr
    
    def get_last_metrics(self) -> Dict:
        """
        Get metrics from the last translation operation.
        
        Returns:
            dict: Performance metrics from last operation
        """
        return self.last_metrics
    
    def get_source_transcription(self):
        """
        Get the stored source language transcription.
        
        Returns:
            str: Source transcription
        """
        return self.source_text
    
    def get_target_transcription(self):
        """
        Get the stored target language translation.
        
        Returns:
            str: Target translation
        """
        return self.target_text
    
    def get_source_language(self):
        """
        Get the detected source language.
        
        Returns:
            str: Source language code
        """
        return self.source_language