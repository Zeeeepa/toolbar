from enum import Enum
from typing import Optional, Union, Tuple
import numpy as np
from scipy import signal
from .logger import logger

class AudioFormat(Enum):
    """Supported audio formats"""
    RAW = "raw"
    WEBM = "webm"
    WAV = "wav"
    MP3 = "mp3"

class AudioProcessor:
    """Audio processing utility class"""
    def __init__(self):
        self.sample_rate = 44100
        self.channels = 1  # Default to mono for speech
        self.bit_depth = 16
        self.noise_reduction_enabled = True
        self.noise_reduction_strength = 0.1
    
    def process_audio(self, audio_data: bytes, format: AudioFormat) -> bytes:
        """Process audio data with noise reduction and normalization"""
        try:
            # Convert bytes to numpy array
            data = np.frombuffer(audio_data, dtype=np.int16)
            
            # Apply noise reduction if enabled
            if self.noise_reduction_enabled:
                data = self._reduce_noise(data)
            
            # Normalize audio
            data = self._normalize_audio(data)
            
            # Convert back to bytes
            return data.tobytes()
        except Exception as e:
            logger.error(f"Error processing audio: {str(e)}")
            return audio_data
    
    def _reduce_noise(self, data: np.ndarray) -> np.ndarray:
        """Apply noise reduction to audio data"""
        try:
            # Convert to float32 for processing
            data = data.astype(np.float32) / 32768.0
            
            # Estimate noise profile from first 1000 samples
            noise_profile = np.mean(np.abs(data[:1000]))
            
            # Apply simple noise gate
            data[np.abs(data) < noise_profile * self.noise_reduction_strength] = 0
            
            # Convert back to int16
            return (data * 32768.0).astype(np.int16)
        except Exception as e:
            logger.error(f"Error reducing noise: {str(e)}")
            return data
    
    def _normalize_audio(self, data: np.ndarray) -> np.ndarray:
        """Normalize audio to use full dynamic range"""
        try:
            # Convert to float32 for processing
            data = data.astype(np.float32)
            
            # Find max amplitude
            max_val = np.max(np.abs(data))
            
            if max_val > 0:
                # Scale to use full range
                data = data * (32767.0 / max_val)
            
            # Convert back to int16
            return data.astype(np.int16)
        except Exception as e:
            logger.error(f"Error normalizing audio: {str(e)}")
            return data
    
    async def extract_audio_blob(self, video: bytes, range: Optional[Tuple[float, float]] = None) -> bytes:
        """Extract audio from video blob"""
        try:
            buffer = video
            audio_ctx = await self._create_audio_context()
            audio_buffer = await audio_ctx.decode_audio_data(buffer)
            
            if range:
                audio_buffer = self._slice_audio_buffer(audio_buffer, range)
            
            return await self._encode_audio_blob(audio_buffer)
        except Exception as e:
            logger.error(f"Error extracting audio: {str(e)}")
            raise
    
    def _slice_audio_buffer(self, audio_buffer, range: Tuple[float, float]) -> bytes:
        """Slice audio buffer to specified range"""
        try:
            start, end = range
            channels = audio_buffer.number_of_channels
            rate = audio_buffer.sample_rate
            start_offset = int(rate * start)
            end_offset = int(rate * end)
            frame_count = end_offset - start_offset
            
            new_buffer = self._create_audio_buffer(channels, frame_count, rate)
            tmp_array = bytearray(frame_count * 4)  # 4 bytes per float32
            
            for channel in range(channels):
                audio_buffer.copy_from_channel(tmp_array, channel, start_offset)
                new_buffer.copy_to_channel(tmp_array, channel, 0)
            
            return new_buffer
        except Exception as e:
            logger.error(f"Error slicing audio buffer: {str(e)}")
            raise
    
    async def _encode_audio_blob(self, audio_buffer) -> bytes:
        """Encode audio buffer to blob"""
        try:
            muxer = self._create_muxer({
                'target': 'array_buffer',
                'audio': {
                    'codec': 'A_OPUS',
                    'number_of_channels': audio_buffer.number_of_channels,
                    'sample_rate': audio_buffer.sample_rate
                }
            })
            
            audio_encoder = await self._create_audio_encoder({
                'output': lambda chunk, meta: muxer.add_audio_chunk(chunk, meta),
                'error': logger.error
            })
            
            await audio_encoder.configure({
                'codec': 'opus',
                'sample_rate': audio_buffer.sample_rate,
                'number_of_channels': audio_buffer.number_of_channels,
                'bitrate': 96000
            })
            
            signal = self._buffer_to_f32_planar(audio_buffer)
            await audio_encoder.encode({
                'format': 'f32-planar',
                'sample_rate': audio_buffer.sample_rate,
                'number_of_channels': audio_buffer.number_of_channels,
                'number_of_frames': len(audio_buffer),
                'timestamp': 0,
                'data': signal
            })
            
            await audio_encoder.flush()
            muxer.finalize()
            
            return muxer.get_buffer()
        except Exception as e:
            logger.error(f"Error encoding audio blob: {str(e)}")
            raise
    
    def _buffer_to_f32_planar(self, input_buffer) -> bytes:
        """Convert audio buffer to planar float32 array"""
        try:
            length = len(input_buffer)
            channels = input_buffer.number_of_channels
            result = bytearray(length * channels * 4)  # 4 bytes per float32
            
            offset = 0
            for i in range(channels):
                data = input_buffer.get_channel_data(i)
                result[offset:offset + len(data)] = data
                offset += len(data)
            
            return bytes(result)
        except Exception as e:
            logger.error(f"Error converting buffer to F32: {str(e)}")
            raise
    
    async def _create_audio_context(self):
        """Create audio context"""
        # This would be implemented by the platform-specific audio API
        pass
    
    def _create_audio_buffer(self, channels: int, frame_count: int, sample_rate: int):
        """Create new audio buffer"""
        # This would be implemented by the platform-specific audio API
        pass
    
    def _create_muxer(self, config: dict):
        """Create audio muxer"""
        # This would be implemented by the platform-specific muxer
        pass
    
    async def _create_audio_encoder(self, config: dict):
        """Create audio encoder"""
        # This would be implemented by the platform-specific encoder
        pass
