import numpy as np
import sounddevice as sd
from openwakeword.model import Model

CHUNK_SAMPLE = 1280 # 80ms of audio at 16kHz
SAMPLE_RATE = 16000

class WakeWordDetector:
    #keyword: which build-in wake to listen for (no "hey Domly" yet)
    #threshold: confidence score (0-1) above which we count it as detected
    def __init__(self, keyword: str = "hey_jarvis", threshold: float = 0.5):
        self.keyword = keyword
        self.threshold = threshold
        self._model = Model(wakeword_models=[keyword])
        
    # open a continuous microphone stream and feeds it to the model
    # 80ms at a time, forever, untill the wake word is heard    
    def listen_for_wake_word(self) -> None:
        with sd.InputStream(samplerate=SAMPLE_RATE, channels=1, dtype="int16") as stream:
            while True:
                chunk, _ = stream.read(CHUNK_SAMPLE)
                audio_chunk = chunk.flatten()
                prediction = self._model.predict(audio_chunk)
                if prediction[self.keyword] >= self.threshold:
                    return
        
        
