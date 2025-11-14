from __future__ import annotations

from pathlib import Path
from typing import Optional

import numpy as np
import requests
from moviepy.audio.io.AudioFileClip import AudioFileClip
from scipy.io import wavfile

from ..config import AppSettings


class AudioGenerationError(RuntimeError):
    """Raised when voice generation fails."""


def _call_tts_api(text: str, settings: AppSettings, output_path: Path) -> Path:
    url = f"{settings.external.tts_api_url}/{settings.external.tts_voice_id}"
    payload = {
        "text": text,
        "model_id": "eleven_monolingual_v1",
        "voice_settings": {"stability": 0.4, "similarity_boost": 0.8},
    }
    headers = {
        "xi-api-key": settings.external.tts_api_key,
        "Content-Type": "application/json",
    }
    response = requests.post(url, json=payload, headers=headers, timeout=120)
    response.raise_for_status()
    output_path.write_bytes(response.content)
    return output_path


def _generate_demo_audio(text: str, output_path: Path) -> Path:
    try:
        import pyttsx3

        engine = pyttsx3.init()
        engine.setProperty("rate", 185)
        engine.save_to_file(text, output_path.as_posix())
        engine.runAndWait()
        return output_path
    except Exception:  # pragma: no cover - fallback when pyttsx3 missing
        duration = max(10, len(text.split()) // 2)
        sample_rate = 22050
        t = np.linspace(0, duration, int(sample_rate * duration), False)
        # Simple synthetic voice-like waveform
        frequencies = np.linspace(160, 220, num=len(text))
        waveform = np.zeros_like(t)
        chunk_size = len(t) // len(frequencies)
        for idx, freq in enumerate(frequencies):
            start = idx * chunk_size
            end = start + chunk_size
            waveform[start:end] = 0.2 * np.sin(2 * np.pi * freq * t[start:end])
        wavfile.write(output_path.as_posix(), sample_rate, waveform.astype(np.float32))
        return output_path


def generate_voiceover(text: str, settings: AppSettings, work_dir: Path) -> Path:
    output_dir = work_dir / "audio"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / "voiceover.wav"

    if settings.runtime.demo_mode or not settings.external.tts_api_key:
        return _generate_demo_audio(text, output_path)

    return _call_tts_api(text, settings, output_path)


def audio_duration(audio_path: Path) -> float:
    clip = AudioFileClip(audio_path.as_posix())
    try:
        return clip.duration
    finally:
        clip.close()


__all__ = ["generate_voiceover", "audio_duration", "AudioGenerationError"]
