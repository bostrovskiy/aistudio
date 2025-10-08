import os
import json
import tempfile
import time
from datetime import datetime
from IPython.display import Audio, display
import ipywidgets as widgets
from openai import OpenAI

def get_openai_api_key():
    key = os.getenv("OPENAI_API_KEY")
    if not key:
        raise ValueError("OPENAI_API_KEY not found in environment variables.")
    return key

def get_serper_api_key():
    key = os.getenv("SERPER_API_KEY")
    if not key:
        raise ValueError("SERPER_API_KEY not found in environment variables.")
    return key

def get_openai_model_name():
    key = os.getenv("OPENAI_MODEL_NAME")
    if not key:
        raise ValueError("OPENAI_MODEL_NAME not found in environment variables.")
    return key

def pretty_print_result(result):
    import json
    print(json.dumps(result, indent=2))

def record_audio_input():
    """Simple file path input for audio transcription - always English"""
    try:
        import os
        import sys
        
        # Use sys.stdout.write instead of print to avoid Rich console conflicts
        sys.stdout.write("Voice input: Please provide the path to your audio file.\n")
        sys.stdout.write("Supported formats: mp3, wav, m4a, ogg, flac\n")
        sys.stdout.write("Example: /path/to/your/audio.mp3 or ./audio.wav\n")
        sys.stdout.write("Note: Audio will be transcribed in English.\n")
        sys.stdout.flush()
        
        file_path = input("Enter audio file path (or press Enter to skip): ").strip()
        
        if not file_path:
            sys.stdout.write("No file path provided.\n")
            sys.stdout.flush()
            return None
            
        # Check if file exists
        if not os.path.exists(file_path):
            sys.stdout.write(f"File not found: {file_path}\n")
            sys.stdout.flush()
            return None
            
        # Read the audio file
        with open(file_path, 'rb') as f:
            audio_data = f.read()
            
        sys.stdout.write(f"Successfully loaded audio file: {file_path}\n")
        sys.stdout.write("Will transcribe in English.\n")
        sys.stdout.flush()
        return audio_data
            
    except Exception as e:
        sys.stdout.write(f"Error loading audio file: {e}\n")
        sys.stdout.flush()
        return None

def transcribe_audio(audio_data, language="en"):
    """Transcribe audio using OpenAI Whisper API"""
    try:
        import sys
        client = OpenAI(api_key=get_openai_api_key())
        
        # Save audio data to temporary file
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_file.write(audio_data)
            temp_file_path = temp_file.name
        
        # Transcribe using Whisper with language specification
        with open(temp_file_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language=language,  # Force English transcription
                response_format="text"  # Get plain text, not JSON
            )
        
        # Clean up temporary file
        os.unlink(temp_file_path)
        
        return transcript.strip()
        
    except Exception as e:
        import sys
        sys.stdout.write(f"Error transcribing audio: {e}\n")
        sys.stdout.flush()
        return None

def text_to_speech(text, voice="alloy"):
    """Convert text to speech using OpenAI TTS API"""
    try:
        import sys
        client = OpenAI(api_key=get_openai_api_key())
        
        # Generate speech
        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text
        )
        
        return response.content
        
    except Exception as e:
        import sys
        sys.stdout.write(f"Error generating speech: {e}\n")
        sys.stdout.flush()
        return None

def play_and_save_audio(audio_content, filename_prefix="audio_output"):
    """Play audio in notebook and save to file"""
    try:
        import sys
        if audio_content is None:
            sys.stdout.write("No audio content to play.\n")
            sys.stdout.flush()
            return
        
        # Generate timestamped filename
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"{filename_prefix}_{timestamp}.mp3"
        filepath = os.path.join(os.getcwd(), filename)
        
        # Save audio to file
        with open(filepath, "wb") as f:
            f.write(audio_content)
        
        # Play audio in notebook
        display(Audio(audio_content, autoplay=True))
        
        sys.stdout.write(f"Audio saved to: {filepath}\n")
        sys.stdout.flush()
        return filepath
        
    except Exception as e:
        import sys
        sys.stdout.write(f"Error playing/saving audio: {e}\n")
        sys.stdout.flush()
        return None