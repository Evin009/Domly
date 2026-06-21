import os
from elevenlabs.client import ElevenLabs
from elevenlabs.play import play as _play_audio
from dotenv import load_dotenv

load_dotenv()

_client = None
DEFAULT_VOICE_ID = "bIHbv24MWmeRgasZH58o"  # "Will - Relaxed Optimist" voice


def _get_client() -> ElevenLabs:
    global _client
    if _client is None:
        _client = ElevenLabs(api_key=os.environ["ELEVENLABS_API_KEY"])
    return _client


def speak(text: str) -> None:
    client = _get_client()
    audio = client.text_to_speech.convert(
        voice_id=DEFAULT_VOICE_ID,
        text=text,
        model_id="eleven_turbo_v2",
    )
    _play_audio(audio)
