"""Training session state management and result detection."""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.training import (
    TrainingResult,
    TrainingSettlementResult,
    _ORGASM_PALAMLV,
    _PLEASURE_ORGASM_MAP,
    _REJECTION_SPIRIT_THRESHOLD,
)
from eral.domain.world import CharacterState, WorldState
from eral.content.palamlv import PalamCurve, palam_level_for_value


@dataclass(slots=True)
class TrainingService:
    palam_curve: PalamCurve | None = None

    def start_session(self, world: WorldState, actor_key: str, position_key: str) -> None:
        world.training_active = True
        world.training_actor_key = actor_key
        world.training_position_key = position_key
        world.training_step_index = 0
        world.training_flags = {}

    def end_session(self, world: WorldState) -> None:
        world.training_active = False
        world.training_actor_key = None
        world.training_position_key = None
        world.training_step_index = 0
        world.training_flags = {}

    def development_value(self, actor: CharacterState, key: str) -> int:
        return actor.get_condition(f"train_{key}")

    def detect_results(self, actor: CharacterState) -> TrainingSettlementResult:
        """Detect orgasm / rejection / interrupt after settlement.

        Called after SettlementService.settle_actor has flushed SOURCE → PALAM.
        """
        results: list[TrainingResult] = []
        spirit = actor.stats.base.get("spirit")
        orgasm_count = 0

        if self.palam_curve is not None:
            for palam_key, result_type in _PLEASURE_ORGASM_MAP.items():
                palam_value = actor.stats.palam.get(palam_key)
                palam_lv = palam_level_for_value(self.palam_curve, palam_value)
                if palam_lv >= _ORGASM_PALAMLV:
                    results.append(result_type)
                    orgasm_count += 1
                    afterglow_key = palam_key + "_afterglow"
                    actor.stats.base.add(afterglow_key, 1)
                    actor.stats.palam.set(palam_key, 0)

        was_rejected = False
        was_interrupted = False

        if spirit <= 0:
            was_interrupted = True
            results.append(TrainingResult.INTERRUPTED)
        elif spirit <= _REJECTION_SPIRIT_THRESHOLD:
            lust = actor.stats.palam.get("lust")
            submission = actor.stats.palam.get("submission")
            obedience = actor.stats.palam.get("obedience")
            if submission + obedience < lust:
                was_rejected = True
                results.append(TrainingResult.REJECTED)

        if orgasm_count > 0:
            actor.stats.base.add("orgasm_afterglow", orgasm_count)
            actor.add_condition("total_orgasm_count", orgasm_count)

        return TrainingSettlementResult(
            results=tuple(results),
            orgasm_count=orgasm_count,
            was_rejected=was_rejected,
            was_interrupted=was_interrupted,
        )

    def add_development(self, actor: CharacterState, key: str, delta: int) -> int:
        return actor.add_condition(f"train_{key}", delta)
