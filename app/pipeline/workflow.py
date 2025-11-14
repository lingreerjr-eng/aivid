from __future__ import annotations


import json
import shutil
import uuid

from ..config import AppSettings
from .assembly import assemble_video
from .ideation import build_metadata, choose_best_concept, generate_concepts
from .schema import ScriptPlan, WorkflowResult
from .scripting import generate_script


def generate_video_story(prompt: str, settings: AppSettings) -> WorkflowResult:
    candidates = generate_concepts(prompt, settings)
    winner = choose_best_concept(candidates)
    script_plan: ScriptPlan = generate_script(winner, prompt, settings)

    run_id = uuid.uuid4().hex[:8]
    work_dir = settings.output_dir / f"run_{run_id}"
    work_dir.mkdir(parents=True, exist_ok=True)
    final_path = settings.output_dir / f"final_{run_id}.mp4"

    assemble_video(
        script_text=script_plan.script_text,
        captions=script_plan.captions,
        shots=script_plan.shots,
        settings=settings,
        work_dir=work_dir,
        final_path=final_path,
    )

    leaderboard, winner_score = build_metadata(candidates, winner)
    metadata = {
        "prompt": prompt,
        "run_id": run_id,
        "idea_leaderboard": leaderboard,
        "winner_score": winner_score,
        "shots": json.dumps([shot.__dict__ for shot in script_plan.shots], indent=2),
    }

    if not settings.runtime.keep_intermediates:
        shutil.rmtree(work_dir, ignore_errors=True)

    return WorkflowResult(
        final_video_path=final_path,
        script_text=script_plan.script_text,
        captions=script_plan.captions,
        final_concept=winner.angle,
        metadata=metadata,
    )


__all__ = ["generate_video_story"]
