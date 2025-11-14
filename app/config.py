from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
import os
from typing import Optional


BASE_DIR = Path(__file__).resolve().parent


def _determine_output_dir() -> Path:
    """Select an output directory that works for local and serverless runs."""

    env_override = os.getenv("AIVID_OUTPUT_DIR")
    if env_override:
        return Path(env_override).expanduser().resolve()

    # Netlify (and many other serverless platforms) only allow writes inside /tmp
    if os.getenv("NETLIFY") or os.getenv("AWS_LAMBDA_FUNCTION_NAME"):
        return Path("/tmp/aivid_outputs")

    return (BASE_DIR / "outputs").resolve()


OUTPUT_DIR = _determine_output_dir()
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


@dataclass
class ExternalAPIConfig:
    ollama_base_url: str = "http://127.0.0.1:11434"
    ollama_model: Optional[str] = "llama3.1"
    video_api_url: str = "https://api.pikalabs.com/v1/videos"
    video_api_key: Optional[str] = None
    tts_api_url: str = "https://api.elevenlabs.io/v1/text-to-speech"
    tts_voice_id: str = "EXAVITQu4vr4xnSDxMaL"
    tts_api_key: Optional[str] = None


@dataclass
class RuntimeFlags:
    demo_mode: bool = False
    keep_intermediates: bool = False


@dataclass
class AppSettings:
    external: ExternalAPIConfig = field(default_factory=ExternalAPIConfig)
    runtime: RuntimeFlags = field(default_factory=RuntimeFlags)
    output_dir: Path = OUTPUT_DIR


def load_settings() -> AppSettings:
    """Load configuration from environment variables."""
    demo_mode = os.getenv("AIVID_DEMO_MODE", "true").lower() in {"1", "true", "yes"}
    keep_intermediates = os.getenv("AIVID_KEEP_INTERMEDIATES", "false").lower() in {"1", "true", "yes"}

    settings = AppSettings(
        external=ExternalAPIConfig(
            ollama_base_url=os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434"),
            ollama_model=os.getenv("OLLAMA_MODEL", "llama3.1"),
            video_api_url=os.getenv("VIDEO_API_URL", "https://api.pikalabs.com/v1/videos"),
            video_api_key=os.getenv("VIDEO_API_KEY"),
            tts_api_url=os.getenv("TTS_API_URL", "https://api.elevenlabs.io/v1/text-to-speech"),
            tts_voice_id=os.getenv("TTS_VOICE_ID", "EXAVITQu4vr4xnSDxMaL"),
            tts_api_key=os.getenv("TTS_API_KEY"),
        ),
        runtime=RuntimeFlags(
            demo_mode=demo_mode,
            keep_intermediates=keep_intermediates,
        ),
    )
    return settings


__all__ = ["AppSettings", "ExternalAPIConfig", "RuntimeFlags", "load_settings"]
