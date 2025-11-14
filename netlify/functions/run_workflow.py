"""Netlify Function entry point for the autonomous video workflow."""

from __future__ import annotations

import base64
import json
import os
import sys
from pathlib import Path
from typing import Any, Dict

# Ensure the app package is importable when the function is bundled.
CURRENT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = CURRENT_DIR.parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from app.config import load_settings
from app.pipeline.workflow import generate_video_story


def _response(status: int, payload: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "statusCode": status,
        "headers": {
            "Content-Type": "application/json",
            "Access-Control-Allow-Origin": "*",
            "Access-Control-Allow-Headers": "Content-Type",
            "Access-Control-Allow-Methods": "POST,OPTIONS",
        },
        "body": json.dumps(payload),
    }


def handler(event: Dict[str, Any], _context: Any) -> Dict[str, Any]:
    if event.get("httpMethod") == "OPTIONS":
        return _response(200, {"ok": True})

    try:
        payload = json.loads(event.get("body") or "{}")
    except json.JSONDecodeError:
        return _response(400, {"error": "Invalid JSON payload."})

    prompt = (payload.get("prompt") or "").strip()
    if not prompt:
        return _response(400, {"error": "Please provide a prompt with 1-3 sentences."})

    result = None
    try:
        settings = load_settings()
        result = generate_video_story(prompt, settings)
        video_bytes = result.final_video_path.read_bytes()
    except Exception as exc:  # pragma: no cover - surfaces runtime issues to client
        return _response(500, {"error": "Video generation failed", "details": str(exc)})
    finally:
        if result is not None:
            try:
                result.final_video_path.unlink(missing_ok=True)
            except Exception:
                pass

    body = {
        "prompt": prompt,
        "final_concept": result.final_concept,
        "script_text": result.script_text,
        "captions": result.captions,
        "metadata": result.metadata,
        "video": {
            "filename": result.final_video_path.name,
            "mime_type": "video/mp4",
            "base64": base64.b64encode(video_bytes).decode("ascii"),
        },
    }

    return _response(200, body)


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Run the video workflow once from the command line.")
    parser.add_argument("prompt", help="A 1-3 sentence idea to turn into a video")
    args = parser.parse_args()

    lambda_event = {"httpMethod": "POST", "body": json.dumps({"prompt": args.prompt})}
    result = handler(lambda_event, None)
    print(f"Status: {result['statusCode']}")
    print(result["body"])
