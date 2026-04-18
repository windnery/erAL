"""Training session domain models."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum


class TrainingResult(StrEnum):
    ORGASM_C = "orgasm_c"
    ORGASM_V = "orgasm_v"
    ORGASM_A = "orgasm_a"
    ORGASM_B = "orgasm_b"
    ORGASM_M = "orgasm_m"
    REJECTED = "rejected"
    INTERRUPTED = "interrupted"


# PALAMLV threshold for orgasm detection
_ORGASM_PALAMLV = 5  # PALAM >= 2000 triggers orgasm

# Pleasure axes that correspond to orgasm types
_PLEASURE_ORGASM_MAP = {
    "pleasure_c": TrainingResult.ORGASM_C,
    "pleasure_v": TrainingResult.ORGASM_V,
    "pleasure_a": TrainingResult.ORGASM_A,
    "pleasure_b": TrainingResult.ORGASM_B,
    "pleasure_m": TrainingResult.ORGASM_M,
}

# Spirit threshold below which rejection may occur
_REJECTION_SPIRIT_THRESHOLD = 10


@dataclass(slots=True)
class TrainingSettlementResult:
    results: tuple[TrainingResult, ...] = ()
    orgasm_count: int = 0
    was_rejected: bool = False
    was_interrupted: bool = False


@dataclass(slots=True)
class TrainingSessionState:
    """Minimal runtime state for an in-progress training session."""

    training_active: bool = False
    training_actor_key: str | None = None
    training_position_key: str | None = None
    training_step_index: int = 0
    training_flags: dict[str, int] = field(default_factory=dict)
