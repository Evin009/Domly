import numpy as np
import sounddevice as sd


# Record from the default micrphone for a fixes number of seconds
def record_audio(duration_seconds: float, sample_rate: int = 16000) -> bytes:
    recording = sd.rec(
        int(duration_seconds * sample_rate),
        samplerate=sample_rate,
        channels=1,
        dtype="int16"
    )
    sd.wait() # blocks untill recording finishes
    return recording.tobytes()

# Converts raw bytes back to numpy array of int16 samples
# then plays it through the default speaker
def play_audio(audio_bytes: bytes, sample_rate: int = 16000) -> None:
    audio_array = np.frombuffer(audio_bytes, dtype="int16")    
    sd.play(audio_array, samplerate=sample_rate)
    sd.wait() #blocks untill playback finshes
    
