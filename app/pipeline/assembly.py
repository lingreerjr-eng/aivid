from __future__ import annotations

from pathlib import Path
from typing import List

from moviepy.editor import AudioFileClip, VideoFileClip

from ..config import AppSettings
from .schema import ShotPlan
from .video import generate_clips, merge_clips
from .audio import generate_voiceover, audio_duration
from .subtitles import build_subtitle_file, burn_subtitles


def assemble_video(
    script_text: str,
    captions: List[str],
    shots: List[ShotPlan],
    settings: AppSettings,
    work_dir: Path,
    final_path: Path,
) -> Path:
    clip_paths = generate_clips(shots, settings, work_dir)
    stitched_path = work_dir / "stitched.mp4"
    merge_clips(clip_paths, stitched_path)

    voiceover_path = generate_voiceover(script_text, settings, work_dir)
    voice_duration = audio_duration(voiceover_path)

    video = VideoFileClip(stitched_path.as_posix())
    audio = AudioFileClip(voiceover_path.as_posix())
    narrated_path = work_dir / "narrated.mp4"
    try:
        video_with_audio = video.set_audio(audio)
        video_with_audio.write_videofile(
            narrated_path.as_posix(),
            fps=24,
            codec="libx264",
            audio_codec="aac",
            verbose=False,
            logger=None,
        )
    finally:
        video.close()
        audio.close()
        if 'video_with_audio' in locals():
            video_with_audio.close()

    subtitle_path = work_dir / "captions.srt"
    build_subtitle_file(captions, voice_duration, subtitle_path)

    burn_subtitles(narrated_path, captions, voice_duration, final_path)
    return final_path


__all__ = ["assemble_video"]
