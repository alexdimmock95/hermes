import whisperx
import librosa
import tempfile
from TTS.api import TTS
from deep_translator import GoogleTranslator

class SpeechToSpeechTranslator:
    """
    Speech-to-speech translation with voice cloning.
    Transcribes audio, translates text, and synthesizes in target language.
    """
    
    def __init__(self, device="cpu", model_size="base", compute_type="int8", batch_size=16):
        """
        Initialize translator.
        
        Args:
            device: "cpu" or "cuda"
            model_size: Whisper model size ("tiny", "base", "small", "medium", "large")
            compute_type: Compute type for model ("int8", "float16", "float32")
            batch_size: Batch size for transcription
        """
        self.device = device
        self.model_size = model_size
        self.compute_type = compute_type
        self.batch_size = batch_size
        
        # Models (initialized as None, loaded later)
        self.model = None  # Whisper model
        self.tts = None    # TTS model

        # Placeholders for transcriptions and languages
        self.source_text = ""
        self.target_text = ""
        self.source_language = ""
        self.target_language = ""
    
    def _load_whisper(self):
        """Load Whisper model (lazy loading)"""
        if self.model is None:
            print(f"Loading {self.model_size} model on {self.device}...")
            self.model = whisperx.load_model(
                self.model_size,
                self.device,
                compute_type=self.compute_type
            )
    
    def _load_tts(self):
        """Load TTS model (lazy loading)"""
        if self.tts is None:
            print("Loading TTS model...")
            self.tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2")
    
    def transcribe(self, audio_path):
        """
        Transcribe audio to text using WhisperX.
        
        Args:
            audio_path: Path to audio file
            
        Returns:
            str: Transcribed text
        """
        self._load_whisper()
        
        # Load audio (same as asr.py)
        audio = whisperx.load_audio(audio_path)

        
        # Transcribe (same as asr.py)
        transcription_result = self.model.transcribe(audio, self.batch_size)
        
        # Handle both dict and list formats (same as asr.py)
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
        
        return text
    
    def translate(self, text, target_language="fr"):
        """
        Translate text to target language.
        
        Args:
            text: Source text (English)
            target_language: Target language code
            
        Returns:
            str: Translated text
        """
        translator = GoogleTranslator(source='auto', target=target_language)
        translated = translator.translate(text)

        # Store translated text and target language
        self.target_text = translated
        self.target_language = target_language

        return translator.translate(text)


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
    
    def synthesize(self, text, speaker_wav, language="fr"):
        """
        Synthesize speech with voice cloning.
        
        Args:
            text: Text to synthesize
            speaker_wav: Path to reference audio for voice cloning
            language: Target language code
            
        Returns:
            tuple: (audio_array, sample_rate)
        """
        self._load_tts()
        
        with tempfile.NamedTemporaryFile(suffix=".wav", delete=False) as tmp:
            self.tts.tts_to_file(
                text=text,
                speaker_wav=speaker_wav,
                language=language,
                file_path=tmp.name
            )
            audio, sr = librosa.load(tmp.name, sr=None)
        
        return audio, sr
    
    def translate_speech(self, audio_path, text=None, target_language="fr"):
        """
        Full pipeline: speech → text → translation → speech.
        
        Args:
            audio_path: Path to input audio
            text: Pre-transcribed text (optional, will transcribe if not provided)
            target_language: Target language code
            
        Returns:
            tuple: (output_audio, sample_rate)
        """
        print("\n" + "="*50)
        print("SPEECH-TO-SPEECH TRANSLATION")
        print("="*50)
        
        # Step 1: Transcribe (if needed)
        if text is None:
            print("\n[1/3] Transcribing audio...")
            text = self.transcribe(audio_path)
            print(f"      Transcribed: '{text}'")
        else:
            print(f"\n[1/3] Using provided text: '{text}'")
            
            # Store provided text and assume English
            self.source_text = text
            self.source_language = "en"  # Assume English if text provided
        
        # Step 2: Translate
        print(f"\n[2/3] Translating to {target_language}...")
        translated_text = self.translate(text, target_language)
        print(f"      Translated: '{translated_text}'")
        
        # Step 3: Synthesize
        print("\n[3/3] Synthesizing with voice cloning...")
        output_audio, sr = self.synthesize(
            translated_text, 
            audio_path, 
            target_language
        )
        print("      ✓ Complete")
        
        return output_audio, sr
    
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