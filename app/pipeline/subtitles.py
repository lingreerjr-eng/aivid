from __future__ import annotations

import datetime as dt
from pathlib import Path
from typing import List, Sequence, Tuple

import numpy as np
import srt
from PIL import Image, ImageDraw, ImageFont
from moviepy.editor import CompositeVideoClip, ImageClip, VideoFileClip


def _subtitle_timings(captions: Sequence[str], audio_duration: float) -> List[Tuple[float, float, str]]:
    if not captions:
        return []
    per_caption = audio_duration / len(captions)
    timings = []
    current = 0.0
    for caption in captions:
        start = current
        end = min(audio_duration, start + per_caption)
        timings.append((start, end, caption))
        current = end
    return timings


def _render_caption_frame(text: str, width: int) -> np.ndarray:
    font = ImageFont.load_default()
    lines = []
    draw_dummy = ImageDraw.Draw(Image.new("RGB", (width, 200), color=(0, 0, 0)))
    words = text.split()
    current: List[str] = []
    max_width = width - 120
    for word in words:
        test_line = " ".join(current + [word])
        if draw_dummy.textlength(test_line, font=font) > max_width and current:
            lines.append(" ".join(current))
            current = [word]
        else:
            current.append(word)
    if current:
        lines.append(" ".join(current))

    text_height = len(lines) * (font.size + 8)
    height = text_height + 40
    image = Image.new("RGBA", (width, height), (0, 0, 0, 0))
    draw = ImageDraw.Draw(image)
    y = 20
    for line in lines:
        line_width = draw.textlength(line, font=font)
        x = (width - line_width) // 2
        draw.text((x, y), line, fill=(255, 255, 255, 255), font=font)
        y += font.size + 8
    return np.array(image)


def build_subtitle_file(captions: Sequence[str], audio_duration: float, output_path: Path) -> Path:
    timings = _subtitle_timings(captions, audio_duration)
    subtitles = []
    for index, (start, end, caption) in enumerate(timings, start=1):
        subtitles.append(
            srt.Subtitle(
                index=index,
                start=dt.timedelta(seconds=start),
                end=dt.timedelta(seconds=end),
                content=caption,
            )
        )
    output_path.write_text(srt.compose(subtitles))
    return output_path


def burn_subtitles(video_path: Path, captions: Sequence[str], audio_duration: float, output_path: Path) -> Path:
    if not captions:
        video_path.replace(output_path)
        return output_path

    clip = VideoFileClip(video_path.as_posix())
    overlays = []
    try:
        width, height = clip.size
        for start, end, caption in _subtitle_timings(captions, audio_duration):
            frame = _render_caption_frame(caption, width)
            overlay = (
                ImageClip(frame)
                .set_duration(max(0.1, end - start))
                .set_start(start)
                .set_position(("center", height - frame.shape[0] - 60))
            )
            overlays.append(overlay)
        composed = CompositeVideoClip([clip] + overlays)
        composed.write_videofile(
            output_path.as_posix(),
            fps=24,
            codec="libx264",
            audio=clip.audio is not None,
            audio_codec="aac",
            verbose=False,
            logger=None,
        )
    finally:
        clip.close()
        for overlay in overlays:
            overlay.close()
        if 'composed' in locals():
            composed.close()
    return output_path


__all__ = ["build_subtitle_file", "burn_subtitles"]
