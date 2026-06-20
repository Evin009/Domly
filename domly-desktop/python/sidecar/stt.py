import os
import io
import wave
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

_client = None


def _get_client() -> OpenAI:
    global _client
    if _client is None:
        _client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])
    return _client


def _to_wav_bytes(audio_bytes: bytes, sample_rate: int) -> io.BytesIO:
    buffer = io.BytesIO()
    with wave.open(buffer, "wb") as wav_file:
        wav_file.setnchannels(1)
        wav_file.setsampwidth(2)
        wav_file.setframerate(sample_rate)
        wav_file.writeframes(audio_bytes)
    buffer.seek(0)
    buffer.name = "audio.wav"
    return buffer


def transcribe(audio_bytes: bytes, sample_rate: int = 16000) -> str:
    client = _get_client()
    wav_buffer = _to_wav_bytes(audio_bytes, sample_rate)
    response = client.audio.transcriptions.create(model="whisper-1", file=wav_buffer)
    return response.text
