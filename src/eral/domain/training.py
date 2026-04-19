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
    COUNTER_KISS = "counter_kiss"
    COUNTER_EMBRACE = "counter_embrace"
    COUNTER_SERVICE = "counter_service"
    COUNTER_REQUEST = "counter_request"


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

# Counter trigger thresholds (ABL-deterministic path — baseline)
_COUNTER_LUST_THRESHOLD = 800
_COUNTER_OBEDIENCE_THRESHOLD = 200
_COUNTER_PLEASURE_TOTAL = 1500

# Counter trigger thresholds (probability path — spec-based)
_COUNTER_LUST_KISS = 2000
_COUNTER_LUST_TOUCH = 5000
_COUNTER_SUBMISSION_REQUEST = 10000
_COUNTER_OBEDIENCE_SERVICE = 4000
_COUNTER_SUBMISSION_SERVICE = 5000
_COUNTER_RANK_LIKE = 2  # 喜欢

# Probability contributions
_COUNTER_PROB_LUST_LOW = 0.15   # lust >= 2000
_COUNTER_PROB_LUST_HIGH = 0.15  # lust >= 5000 (additive)
_COUNTER_PROB_SUBMISSION = 0.10  # submission >= 3000
_COUNTER_PROB_OBEDIENCE = 0.10  # obedience >= 2000
_COUNTER_PROB_RANK_LIKE = 0.10
_COUNTER_PROB_MARK_PLEASURE = 0.10  # pleasure_mark >= 2
_COUNTER_PROB_MARK_SUBMISSION = 0.20  # submission_mark >= 3
_COUNTER_PROB_CAP = 0.80


@dataclass(slots=True)
class TrainingSettlementResult:
    results: tuple[TrainingResult, ...] = ()
    orgasm_count: int = 0
    was_rejected: bool = False
    was_interrupted: bool = False
    counter: TrainingResult | None = None


@dataclass(slots=True)
class TrainingSessionState:
    """Minimal runtime state for an in-progress training session."""

    training_active: bool = False
    training_actor_key: str | None = None
    training_position_key: str | None = None
    training_step_index: int = 0
    training_flags: dict[str, int] = field(default_factory=dict)
