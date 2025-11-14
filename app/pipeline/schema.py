from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Dict, List


@dataclass
class ConceptCandidate:
    angle: str
    hook: str
    score: float


@dataclass
class ShotPlan:
    scene_number: int
    description: str
    duration: float
    prompt: str


@dataclass
class ScriptPlan:
    final_concept: ConceptCandidate
    script_text: str
    shots: List[ShotPlan]
    captions: List[str]


@dataclass
class WorkflowResult:
    final_video_path: Path
    script_text: str
    captions: List[str]
    final_concept: str
    metadata: Dict[str, str] = field(default_factory=dict)


__all__ = [
    "ConceptCandidate",
    "ShotPlan",
    "ScriptPlan",
    "WorkflowResult",
]
