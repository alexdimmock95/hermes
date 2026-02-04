# app.py

import gradio as gr
import soundfile as sf
import numpy as np
import sys
from pathlib import Path

# Add project root to path
sys.path.append(str(Path(__file__).parent.parent))

# Import modules
from src.denoiser import Denoiser
from src.voice_transformer import VoiceTransformer
from src.speech_to_speech import SpeechToSpeechTranslator

def process_audio(audio_file, mode, voice_transform_type=None, target_lang=None):
    """
    Main processing function called by Gradio.
    
    This wraps your existing pipeline logic in a single function.
    """
    
    if audio_file is None:
        return None, "⚠️ Please upload or record audio first", "", ""
        
    try:
        # Step 1: Load audio
        audio, sr = sf.read(audio_file)
        if audio.ndim > 1:
            audio = np.mean(audio, axis=1)
        audio = audio.astype(np.float32)
        
        # Step 2: Denoise
        denoiser = Denoiser(model_name="DeepFilterNet3", post_filter=True)
        audio = denoiser.process_frame(audio)
        
        # Step 3: Process based on mode
        if mode == "Voice Transformation":
            transformer = VoiceTransformer()
            
            if voice_transform_type == "Male → Female":
                output = transformer.preset_male_to_female(audio, sr)
            elif voice_transform_type == "Female → Male":
                output = transformer.preset_female_to_male(audio, sr)
            elif voice_transform_type == "Older":
                output = transformer.preset_older(audio, sr)
            else:  # Younger
                output = transformer.preset_younger(audio, sr)
            
            status = f"✅ Voice transformed: {voice_transform_type}"
        
            input_transcription = ""
            output_transcription = ""

        else:  # Translation mode
            translator = SpeechToSpeechTranslator(
                device="cpu",
                model_size="base",
                compute_type="int8"
            )
            
            # Save temp file for translator
            temp_path = "temp_input.wav"
            sf.write(temp_path, audio, sr)
            
            output, sr = translator.translate_speech(
                audio_path=temp_path,
                target_language=target_lang
            )
            
            # Get transcriptions and detected language
            try:
                input_transcription = translator.get_source_transcription()
                output_transcription = translator.get_target_transcription()
                source_lang = translator.get_source_language()
                source_lang_name = get_language_name(source_lang)
                target_lang_name = get_language_name(target_lang)
                status = f"✅ Translated from {source_lang_name} to {target_lang_name}"


            except AttributeError:
                # Fallback if methods don't exist yet
                input_transcription = "[Transcription available after updating SpeechToSpeechTranslator]"
                output_transcription = "[Translation text available after updating SpeechToSpeechTranslator]"
                status = f"✅ Translated to {get_language_name(target_lang)}"
        
        # Save output
        output_path = "temp_output.wav"
        sf.write(output_path, output, sr)
        
        return output_path, status, input_transcription, output_transcription
        
    except Exception as e:
        return None, f"❌ Error: {str(e)}", "", ""

def get_language_name(code):
    """Get full language name from code"""
    lang_map = {
        "en": "English",
        "es": "Spanish",
        "fr": "French",
        "de": "German",
        "it": "Italian",
        "pt": "Portuguese",
        "pl": "Polish",
        "tr": "Turkish",
        "ru": "Russian",
        "nl": "Dutch",
        "cs": "Czech",
        "ar": "Arabic",
        "zh-cn": "Chinese",
        "zh": "Chinese",  # Alternative code
        "ja": "Japanese",
        "hu": "Hungarian",
        "ko": "Korean",
        "hi": "Hindi"
    }
    return lang_map.get(code, code.upper())

# Build Gradio interface
with gr.Blocks(
    title="Audio Processing Pipeline",
    theme=gr.themes.Soft()
) as demo:
    
    gr.Markdown("# 🎙️ Audio Processing Pipeline")
    gr.Markdown("Clean, transform, and translate your audio with AI")
    
    with gr.Row():
        # Left column - inputs
        with gr.Column(scale=1):
            gr.Markdown("### Input")
            audio_input = gr.Audio(
                type="filepath",
                label="Audio Input",
                sources=["upload", "microphone"]
            )
            
            mode = gr.Radio(
                ["Voice Transformation", "Translation"],
                label="Processing Mode",
                value="Voice Transformation"
            )
            
            # Conditional inputs based on mode
            voice_transform_type = gr.Radio(
                ["Male → Female", "Female → Male", "Older", "Younger"],
                label="Transformation Type",
                value="Male → Female",
                visible=True
            )
            
            target_lang = gr.Dropdown(
                choices=[
                    ("English", "en"),
                    ("Spanish", "es"),
                    ("French", "fr"),
                    ("German", "de"),
                    ("Italian", "it"),
                    ("Portuguese", "pt"),
                    ("Polish", "pl"),
                    ("Turkish", "tr"),
                    ("Russian", "ru"),
                    ("Dutch", "nl"),
                    ("Czech", "cs"),
                    ("Arabic", "ar"),
                    ("Chinese (Mandarin)", "zh-cn"),
                    ("Japanese", "ja"),
                    ("Hungarian", "hu"),
                    ("Korean", "ko"),
                    ("Hindi", "hi")
                ],
                label="Target Language",
                value="fr",
                visible=False
            )
            
            process_btn = gr.Button("🎯 Process Audio", variant="primary", size="lg")
        
        # Right column - outputs
        with gr.Column(scale=1):
            gr.Markdown("### Output")
            audio_output = gr.Audio(label="Processed Audio")
            status_output = gr.Textbox(
                label="Status",
                placeholder="Ready to process...",
                interactive=False
            )
    
    # Transcription section - side by side
    with gr.Row():
        with gr.Column(scale=1):
            gr.Markdown("### Input Transcription")
            input_transcription = gr.Textbox(
                label="Original Audio Text",
                placeholder="Input transcription...",
                lines=5,
                interactive=False
            )
        
        with gr.Column(scale=1):
            gr.Markdown("### Output Translation")
            output_transcription = gr.Textbox(
                label="Translated Text",
                placeholder=f"{target_lang}",
                lines=5,
                interactive=False
            )
    
    # Show/hide inputs based on mode
    def update_visibility(mode):
        if mode == "Voice Transformation":
            return gr.update(visible=True), gr.update(visible=False)
        else:
            return gr.update(visible=False), gr.update(visible=True)
    
    mode.change(
        update_visibility,
        inputs=[mode],
        outputs=[voice_transform_type, target_lang]
    )
    
    # Process button click
    process_btn.click(
        fn=process_audio,
        inputs=[audio_input, mode, voice_transform_type, target_lang],
        outputs=[audio_output, status_output, input_transcription, output_transcription]
    )

if __name__ == "__main__":
    demo.launch(
        inbrowser=True,
        share=True,
        server_name="127.0.0.1",  # Access from network
        server_port=7860
    )



## TODO: 6. Custom Voice Cloning. Effort: Medium (1 day). Value: HIGH. Add: Upload a target voice → clone it for translations. 
## TODO: 7. Real-time Translation. Effort: High (2 days). Value: HIGH (if people use it live). Add: Stream audio input → translate on-the-fly
## TODO: 11. Multi-Speaker Diarization. Effort: High (3 days). Value: HIGH for podcasts/meetings. Add: Detect multiple speakers → translate each separately

'''
🚀 Launch Checklist
Before putting on GitHub:
Code Quality

 Add proper error handling
 Remove debug print statements
 Add docstrings to main functions
 Clean up commented-out code

Documentation

 Good README with:

 What it does (1 sentence)
 Demo GIF/video
 Installation instructions
 Usage examples
 Supported languages list


 LICENSE file (MIT recommended)
 requirements.txt with all dependencies

User Experience

 Add example audio files
 Add "About" section in UI
 Add error messages that help users fix issues
 Test on clean install (does it work out of the box?)

Optional but Nice

 Add GitHub Actions CI/CD
 Add contribution guidelines
 Add badges (build status, license, etc.)
 Add demo deployment (Hugging Face Spaces is free!)
 '''