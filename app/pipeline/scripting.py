from __future__ import annotations

import json
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


def _extract_json_payload(text: str) -> dict:
    cleaned = text.strip()
    if cleaned.startswith("```"):
        cleaned = "\n".join(
            line for line in cleaned.splitlines() if not line.strip().startswith("```")
        ).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError as exc:
        raise ValueError("Failed to parse JSON from Ollama response") from exc


def _call_ollama(concept: ConceptCandidate, topic: str, settings: AppSettings) -> ScriptPlan:
    payload = {
        "model": settings.external.ollama_model,
        "messages": [
            {"role": "system", "content": "You create production-ready short form scripts. Respond strictly in JSON."},
            {
                "role": "user",
                "content": SCRIPT_PROMPT.format(concept=concept.angle, hook=concept.hook, topic=topic),
            },
        ],
        "stream": False,
    }
    base_url = settings.external.ollama_base_url.rstrip("/")
    response = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=120,
    )
    response.raise_for_status()
    data = response.json()
    text = data.get("message", {}).get("content", "").strip()
    if not text:
        raise ValueError("Ollama response did not include content")
    parsed = _extract_json_payload(text)

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
    if settings.runtime.demo_mode or not settings.external.ollama_model:
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

    return _call_ollama(concept, topic, settings)


__all__ = ["generate_script"]
