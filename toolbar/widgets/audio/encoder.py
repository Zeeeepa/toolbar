import numpy as np
import sounddevice as sd
from typing import Optional, Tuple, Union
import webrtcvad
import wave
import io

class AudioEncoder:
    def __init__(self, sample_rate: int = 16000, channels: int = 1):
        """Initialize the audio encoder.
        
        Args:
            sample_rate: Sample rate in Hz (default: 16000)
            channels: Number of audio channels (default: 1)
        """
        self.sample_rate = sample_rate
        self.channels = channels
        self.vad = webrtcvad.Vad(3)  # Aggressiveness level 3
        
    def record_audio(self, duration: float) -> np.ndarray:
        """Record audio for specified duration.
        
        Args:
            duration: Recording duration in seconds
            
        Returns:
            Recorded audio as numpy array
        """
        audio = sd.rec(
            int(duration * self.sample_rate),
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=np.float32
        )
        sd.wait()
        return audio
        
    def encode_audio(self, audio: np.ndarray) -> bytes:
        """Encode audio data to WAV format.
        
        Args:
            audio: Audio data as numpy array
            
        Returns:
            WAV-encoded audio bytes
        """
        buffer = io.BytesIO()
        with wave.open(buffer, 'wb') as wf:
            wf.setnchannels(self.channels)
            wf.setsampwidth(2)  # 16-bit audio
            wf.setframerate(self.sample_rate)
            wf.writeframes((audio * 32767).astype(np.int16).tobytes())
        return buffer.getvalue()
        
    def decode_audio(self, audio_bytes: bytes) -> np.ndarray:
        """Decode WAV audio bytes to numpy array.
        
        Args:
            audio_bytes: WAV-encoded audio bytes
            
        Returns:
            Decoded audio as numpy array
        """
        buffer = io.BytesIO(audio_bytes)
        with wave.open(buffer, 'rb') as wf:
            audio = np.frombuffer(wf.readframes(wf.getnframes()), dtype=np.int16)
            audio = audio.astype(np.float32) / 32767
            return audio.reshape(-1, wf.getnchannels())
            
    def detect_speech(self, audio: np.ndarray, frame_duration: int = 30) -> np.ndarray:
        """Detect speech segments in audio using VAD.
        
        Args:
            audio: Audio data as numpy array
            frame_duration: Frame duration in milliseconds
            
        Returns:
            Audio with non-speech segments zeroed out
        """
        frame_len = int(self.sample_rate * frame_duration / 1000)
        audio_int16 = (audio * 32767).astype(np.int16)
        
        result = np.zeros_like(audio)
        for i in range(0, len(audio), frame_len):
            frame = audio_int16[i:i+frame_len]
            if len(frame) == frame_len:  # Skip partial frames
                if self.vad.is_speech(frame.tobytes(), self.sample_rate):
                    result[i:i+frame_len] = audio[i:i+frame_len]
                    
        return result
