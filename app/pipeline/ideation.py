from __future__ import annotations

import json
import random
from typing import List, Tuple

import requests

from ..config import AppSettings
from .schema import ConceptCandidate

SYSTEM_PROMPT = (
    "You are an elite short-form video growth strategist. Given a topic, generate "
    "distinct viral video angles with a hook and a 0-100 virality score."
)


IDEA_PROMPT = """
Topic: {topic}
Respond with JSON array of objects using keys angle, hook, score.
"""


DEMO_ANGLES = [
    ("Unexpected transformation", "Watch this {topic} idea come alive in 20 seconds", 82.0),
    ("Rapid fire tips", "3 secrets about {topic} nobody tells you", 77.0),
    ("Myth busting", "Stop believing this {topic} lie", 75.0),
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


def _call_ollama(topic: str, settings: AppSettings) -> List[ConceptCandidate]:
    payload = {
        "model": settings.external.ollama_model,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT + " Respond strictly in JSON."},
            {"role": "user", "content": IDEA_PROMPT.format(topic=topic)},
        ],
        "stream": False,
    }

    base_url = settings.external.ollama_base_url.rstrip("/")
    response = requests.post(
        f"{base_url}/api/chat",
        json=payload,
        timeout=90,
    )
    response.raise_for_status()
    data = response.json()
    text = data.get("message", {}).get("content", "").strip()
    if not text:
        raise ValueError("Ollama response did not include content")

    parsed = _extract_json_payload(text)
    candidates = [
        ConceptCandidate(
            angle=item["angle"],
            hook=item["hook"],
            score=float(item.get("score", 0)),
        )
        for item in parsed.get("angles", [])
    ]
    if not candidates:
        raise ValueError("Model did not return any angles")
    return candidates


def generate_concepts(topic: str, settings: AppSettings) -> List[ConceptCandidate]:
    if settings.runtime.demo_mode or not settings.external.ollama_model:
        rng = random.Random(hash(topic) & 0xFFFFFFFF)
        return [
            ConceptCandidate(angle.format(topic=topic), hook.format(topic=topic), score + rng.random() * 10)
            for angle, hook, score in DEMO_ANGLES
        ]

    return _call_ollama(topic, settings)


def choose_best_concept(candidates: List[ConceptCandidate]) -> ConceptCandidate:
    if not candidates:
        raise ValueError("No concept candidates available")
    best = max(candidates, key=lambda c: c.score)
    # Add tiny deterministic tie breaker for reproducibility
    tie_breaker = sum(ord(ch) for ch in best.angle) % 0.01
    return ConceptCandidate(angle=best.angle, hook=best.hook, score=best.score + tie_breaker)


def build_metadata(candidates: List[ConceptCandidate], winner: ConceptCandidate) -> Tuple[str, str]:
    ranked = sorted(candidates, key=lambda c: c.score, reverse=True)
    leaderboard = ", ".join(f"{c.angle} ({c.score:.1f})" for c in ranked)
    return leaderboard, f"winner_score:{winner.score:.2f}"


__all__ = ["generate_concepts", "choose_best_concept", "build_metadata"]
