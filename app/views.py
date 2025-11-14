from __future__ import annotations

from flask import Flask, render_template, request
from werkzeug.utils import secure_filename

from .config import AppSettings
from .pipeline.workflow import generate_video_story


class PipelineError(RuntimeError):
    """Raised when the pipeline fails."""


def register_routes(app: Flask) -> None:
    @app.get("/")
    def index():
        return render_template("index.html")

    @app.post("/generate")
    def generate():
        prompt = request.form.get("prompt", "").strip()
        if not prompt:
            return render_template("index.html", error="Please provide a topic or short prompt."), 400

        settings: AppSettings = app.config["APP_SETTINGS"]

        try:
            result = generate_video_story(prompt, settings)
        except Exception as exc:  # pragma: no cover - top level guard
            raise PipelineError(str(exc)) from exc

        # Ensure the output file is downloadable within static directory
        filename = secure_filename(result.final_video_path.name)
        download_path = f"outputs/{filename}"

        return render_template(
            "result.html",
            prompt=prompt,
            final_video_url=f"/static/{download_path}",
            final_video_path=result.final_video_path,
            script=result.script_text,
            captions=result.captions,
            idea=result.final_concept,
            metadata=result.metadata,
        )


__all__ = ["register_routes", "PipelineError"]
