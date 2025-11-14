from __future__ import annotations

import json
import math
from typing import List

import requests

from ..config import AppSettings
from .schema import ConceptCandidate, ScriptPlan, ShotPlan


SCRIPT_PROMPT = """
You are a viral short-form storyteller. Create a 15-30 second video plan.
Respond in JSON with keys script, captions (array), and shots (array of objects with scene_number, description, prompt, duration_seconds).
Concept to amplify: {concept}
Hook: {hook}
"""


DEMO_SCRIPT = (
    "You won't believe how fast this {topic} idea works. First, set the stage with a quick challenge. "
    "Then reveal the transformation, and end with a punchy call to action."
)


DEMO_CAPTIONS = [
    "This {topic} hack is wild",
    "3 steps in 20 seconds",
    "Ready to try it?",
]


def _call_openai(concept: ConceptCandidate, topic: str, settings: AppSettings) -> ScriptPlan:
    payload = {
        "model": settings.external.openai_model,
        "messages": [
            {"role": "system", "content": "You create production-ready short form scripts."},
            {
                "role": "user",
                "content": SCRIPT_PROMPT.format(concept=concept.angle, hook=concept.hook, topic=topic),
            },
        ],
        "response_format": {"type": "json_object"},
    }
    headers = {
        "Authorization": f"Bearer {settings.external.openai_api_key}",
        "Content-Type": "application/json",
    }
    response = requests.post(
        "https://api.openai.com/v1/responses",
        json=payload,
        headers=headers,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    text = data["output"]["text"] if "output" in data else data["choices"][0]["message"]["content"]
    parsed = json.loads(text)

    script = parsed["script"].strip()
    captions = [str(item).strip() for item in parsed.get("captions", [])]
    shots = [
        ShotPlan(
            scene_number=int(item.get("scene_number", idx + 1)),
            description=item.get("description", ""),
            duration=float(item.get("duration_seconds", 5.0)),
            prompt=item.get("prompt", ""),
        )
        for idx, item in enumerate(parsed.get("shots", []))
    ]
    if not shots:
        raise ValueError("Script generator returned no shots")
    return ScriptPlan(final_concept=concept, script_text=script, shots=shots, captions=captions)


def generate_script(concept: ConceptCandidate, topic: str, settings: AppSettings) -> ScriptPlan:
    if settings.runtime.demo_mode or not settings.external.openai_api_key:
        shots = [
            ShotPlan(
                scene_number=1,
                description=f"Close-up intro with bold text about {topic}",
                duration=5.0,
                prompt=f"Vibrant intro shot for {topic}",
            ),
            ShotPlan(
                scene_number=2,
                description=f"Fast cut showing the key {topic} payoff",
                duration=7.0,
                prompt=f"Dynamic depiction of {topic} success",
            ),
            ShotPlan(
                scene_number=3,
                description="End card with CTA and energetic motion",
                duration=5.0,
                prompt=f"High energy outro about {topic}",
            ),
        ]
        script = DEMO_SCRIPT.format(topic=topic)
        captions = [caption.format(topic=topic) for caption in DEMO_CAPTIONS]
        return ScriptPlan(final_concept=concept, script_text=script, shots=shots, captions=captions)

    return _call_openai(concept, topic, settings)


__all__ = ["generate_script"]
