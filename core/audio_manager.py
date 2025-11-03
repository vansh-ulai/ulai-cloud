import logging
import os
import tempfile
import subprocess
from gtts import gTTS

# Primary PulseAudio sink used for TTS output
BOT_SINK_NAME = "TTS_Sink"
FALLBACK_SINK = "Meet_Output"

def speak_text_virtual(text: str):
    """
    Generates TTS using gTTS, converts it to WAV via ffmpeg,
    and plays it through the PulseAudio sink ('TTS_Sink').
    """
    if not text:
        return

    temp_file_name = None
    wav_temp_file_name = None

    try:
        # Generate MP3 speech with gTTS
        tts = gTTS(text=text, lang="en")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tts.save(f.name)
            temp_file_name = f.name

        # Convert to WAV (for paplay)
        wav_temp_file_name = temp_file_name.replace(".mp3", ".wav")
        subprocess.run(
            [
                "ffmpeg", "-y",
                "-i", temp_file_name,
                "-acodec", "pcm_s16le",
                "-ar", "44100",
                "-ac", "2",
                wav_temp_file_name
            ],
            check=True,
            capture_output=True
        )

        # Attempt playback on main sink
        logging.info(f"Speaking into PulseAudio sink: '{BOT_SINK_NAME}'")
        try:
            subprocess.run(
                ["paplay", "--device=" + BOT_SINK_NAME, wav_temp_file_name],
                check=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=30
            )
        except subprocess.CalledProcessError as e:
            # Fallback if main sink doesn't exist
            if "No such entity" in e.stderr.decode():
                logging.warning(f"⚠️ Sink '{BOT_SINK_NAME}' not found. Falling back to '{FALLBACK_SINK}'.")
                subprocess.run(["paplay", "--device=" + FALLBACK_SINK, wav_temp_file_name], check=True)
            else:
                raise
        logging.info("Speech finished successfully.")

    except subprocess.CalledProcessError as e:
        logging.error(f"Error in paplay/ffmpeg: {e.stderr.decode()}")
    except subprocess.TimeoutExpired:
        logging.error("Error: 'paplay' or 'ffmpeg' command timed out.")
    except FileNotFoundError:
        logging.error("Error: 'paplay' or 'ffmpeg' not found. Ensure pulseaudio-utils and ffmpeg are installed.")
    except Exception as e:
        logging.exception(f"TTS playback error: {e}")
    finally:
        # Clean up temporary files
        for path in [temp_file_name, wav_temp_file_name]:
            if path and os.path.exists(path):
                os.remove(path)
