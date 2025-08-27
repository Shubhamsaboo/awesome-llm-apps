import threading
import time
from typing import Optional

import numpy as np
import sounddevice as sd


class AudioPlayer:
    """A simple audio player using sounddevice for real-time audio playback."""
    
    def __init__(self, sample_rate: int = 24000, channels: int = 1, dtype=np.int16):
        self.sample_rate = sample_rate
        self.channels = channels
        self.dtype = dtype
        self.stream: Optional[sd.OutputStream] = None
        self._stop_event = threading.Event()
    
    def __enter__(self):
        """Context manager entry - start the audio stream."""
        self.stream = sd.OutputStream(
            samplerate=self.sample_rate,
            channels=self.channels,
            dtype=self.dtype
        )
        self.stream.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - stop and close the audio stream."""
        if self.stream:
            self.stream.stop()
            self.stream.close()
    
    def add_audio(self, audio_data: np.ndarray):
        """Add audio data to be played immediately."""
        if self.stream and not self._stop_event.is_set():
            try:
                self.stream.write(audio_data)
            except Exception as e:
                print(f"[error] Failed to play audio: {e}")
    
    def stop(self):
        """Stop the audio player."""
        self._stop_event.set()


def record_audio(
    duration: float = 5.0,
    sample_rate: int = 24000,
    channels: int = 1,
    dtype=np.int16
) -> np.ndarray:
    """
    Record audio from the microphone for a specified duration.
    
    Args:
        duration: Recording duration in seconds
        sample_rate: Audio sample rate (Hz)
        channels: Number of audio channels
        dtype: Audio data type
    
    Returns:
        Recorded audio as numpy array
    """
    print(f"🎤 Recording audio for {duration} seconds... Press Ctrl+C to stop early.")
    print("Say something now!")
    
    try:
        # Record audio
        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=channels,
            dtype=dtype
        )
        
        # Wait for recording to complete
        sd.wait()
        
        print("✅ Recording completed!")
        
        # Convert to 1D array if mono
        if channels == 1:
            recording = recording.flatten()
        
        return recording.astype(dtype)
        
    except KeyboardInterrupt:
        print("\n⏹️ Recording stopped by user.")
        sd.stop()
        if 'recording' in locals():
            return recording[:int(time.time() * sample_rate)].astype(dtype)
        else:
            # Return empty array if no recording was captured
            return np.zeros(sample_rate, dtype=dtype)
    
    except Exception as e:
        print(f"❌ Recording failed: {e}")
        return np.zeros(sample_rate, dtype=dtype)


def create_silence(duration: float = 1.0, sample_rate: int = 24000, dtype=np.int16) -> np.ndarray:
    """
    Create a buffer of silence for the specified duration.
    
    Args:
        duration: Duration of silence in seconds
        sample_rate: Audio sample rate (Hz)
        dtype: Audio data type
    
    Returns:
        Silence buffer as numpy array
    """
    return np.zeros(int(duration * sample_rate), dtype=dtype)


def save_audio(audio_data: np.ndarray, filename: str, sample_rate: int = 24000):
    """
    Save audio data to a WAV file.
    
    Args:
        audio_data: Audio data as numpy array
        filename: Output filename (should end with .wav)
        sample_rate: Audio sample rate (Hz)
    """
    try:
        import soundfile as sf
        sf.write(filename, audio_data, sample_rate)
        print(f"✅ Audio saved to {filename}")
    except ImportError:
        print("❌ soundfile package required for saving audio. Install with: pip install soundfile")
    except Exception as e:
        print(f"❌ Failed to save audio: {e}")


def load_audio(filename: str, sample_rate: int = 24000, dtype=np.int16) -> np.ndarray:
    """
    Load audio data from a WAV file.
    
    Args:
        filename: Input filename
        sample_rate: Target sample rate (will resample if different)
        dtype: Target data type
    
    Returns:
        Audio data as numpy array
    """
    try:
        import soundfile as sf
        audio_data, original_sr = sf.read(filename)
        
        # Resample if necessary
        if original_sr != sample_rate:
            import librosa
            audio_data = librosa.resample(audio_data, orig_sr=original_sr, target_sr=sample_rate)
        
        # Convert to target dtype
        if dtype == np.int16:
            audio_data = (audio_data * 32767).astype(np.int16)
        
        return audio_data
        
    except ImportError:
        print("❌ soundfile and librosa packages required for loading audio.")
        print("Install with: pip install soundfile librosa")
        return np.zeros(sample_rate, dtype=dtype)
    except Exception as e:
        print(f"❌ Failed to load audio: {e}")
        return np.zeros(sample_rate, dtype=dtype)
