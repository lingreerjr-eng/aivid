from __future__ import annotations

from pathlib import Path
from typing import List

import numpy as np
import requests
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import ImageClip, VideoFileClip, concatenate_videoclips

from ..config import AppSettings
from .schema import ShotPlan

ASPECT_RATIO = (1080, 1920)


class VideoGenerationError(RuntimeError):
    """Raised when the external video API fails."""


def _call_video_api(shot: ShotPlan, settings: AppSettings, output_dir: Path) -> Path:
    payload = {
        "prompt": shot.prompt,
        "aspect_ratio": "9:16",
        "duration": shot.duration,
    }
    headers = {
        "Authorization": f"Bearer {settings.external.video_api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        settings.external.video_api_url,
        json=payload,
        headers=headers,
        timeout=180,
    )
    response.raise_for_status()
    data = response.json()
    download_url = data.get("video_url") or data.get("data", {}).get("url")
    if not download_url:
        raise VideoGenerationError("Video API response missing video URL")
    content = requests.get(download_url, timeout=180)
    content.raise_for_status()
    clip_path = output_dir / f"shot_{shot.scene_number}.mp4"
    clip_path.write_bytes(content.content)
    return clip_path


def _create_text_image(text: str) -> Image.Image:
    width, height = ASPECT_RATIO
    image = Image.new("RGB", (width, height), color=(18, 18, 18))
    draw = ImageDraw.Draw(image)
    font = ImageFont.load_default()
    lines = []
    words = text.split()
    current_line = []
    max_width = width - 120
    for word in words:
        test_line = " ".join(current_line + [word])
        line_width = draw.textlength(test_line, font=font)
        if line_width > max_width and current_line:
            lines.append(" ".join(current_line))
            current_line = [word]
        else:
            current_line.append(word)
    if current_line:
        lines.append(" ".join(current_line))

    total_text_height = len(lines) * (font.size + 12)
    y = (height - total_text_height) // 2
    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = (width - line_width) // 2
        draw.text((x, y), line, fill=(255, 255, 255), font=font)
        y += font.size + 12
    return image


def _generate_demo_clip(shot: ShotPlan, output_dir: Path) -> Path:
    image = _create_text_image(shot.description)
    frame = np.array(image)
    clip = ImageClip(frame).set_duration(max(shot.duration, 2.0))
    clip_path = output_dir / f"demo_shot_{shot.scene_number}.mp4"
    clip.write_videofile(
        clip_path.as_posix(),
        fps=24,
        codec="libx264",
        audio=False,
        verbose=False,
        logger=None,
    )
    clip.close()
    return clip_path


def generate_clips(shots: List[ShotPlan], settings: AppSettings, work_dir: Path) -> List[Path]:
    output_dir = work_dir / "clips"
    output_dir.mkdir(parents=True, exist_ok=True)
    clip_paths: List[Path] = []
    for shot in shots:
        if settings.runtime.demo_mode or not settings.external.video_api_key:
            clip_paths.append(_generate_demo_clip(shot, output_dir))
        else:
            clip_paths.append(_call_video_api(shot, settings, output_dir))
    return clip_paths


def merge_clips(clip_paths: List[Path], final_path: Path) -> Path:
    video_files = [VideoFileClip(path.as_posix()) for path in clip_paths]
    try:
        final_clip = concatenate_videoclips(video_files, method="compose")
        final_clip.write_videofile(
            final_path.as_posix(),
            fps=24,
            codec="libx264",
            audio=False,
            verbose=False,
            logger=None,
        )
    finally:
        for clip in video_files:
            clip.close()
        if 'final_clip' in locals():
            final_clip.close()
    return final_path


__all__ = ["generate_clips", "merge_clips", "VideoGenerationError"]
