"""Constants for the create_plan workflow."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum


class FailureCategory(Enum):
    """Maps 1:1 to failure label IDs in labels.json."""

    GENERAL = "planning_failed"
    LLM_TIMEOUT = "planning_llm_timeout"
    PREREQ_FAILED = "planning_prereq_failed"


@dataclass(frozen=True)
class WorkflowFailure:
    """Structured failure info for the create_plan workflow."""

    category: FailureCategory
    stage: str
    message: str
    prompt_stage: int | None = None
    elapsed_time: float | None = None
