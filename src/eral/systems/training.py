"""Training session state management and result detection."""

from __future__ import annotations

import random
from dataclasses import dataclass, field

from eral.domain.training import (
    TrainingResult,
    TrainingSettlementResult,
    _COUNTER_LUST_THRESHOLD,
    _COUNTER_OBEDIENCE_THRESHOLD,
    _COUNTER_PLEASURE_TOTAL,
    _COUNTER_LUST_KISS,
    _COUNTER_LUST_TOUCH,
    _COUNTER_SUBMISSION_REQUEST,
    _COUNTER_OBEDIENCE_SERVICE,
    _COUNTER_SUBMISSION_SERVICE,
    _COUNTER_RANK_LIKE,
    _COUNTER_PROB_LUST_LOW,
    _COUNTER_PROB_LUST_HIGH,
    _COUNTER_PROB_SUBMISSION,
    _COUNTER_PROB_OBEDIENCE,
    _COUNTER_PROB_RANK_LIKE,
    _COUNTER_PROB_MARK_PLEASURE,
    _COUNTER_PROB_MARK_SUBMISSION,
    _COUNTER_PROB_CAP,
    _ORGASM_PALAMLV,
    _PLEASURE_ORGASM_MAP,
    _REJECTION_SPIRIT_THRESHOLD,
)
from eral.domain.world import CharacterState, WorldState
from eral.content.palamlv import PalamCurve, palam_level_for_value


@dataclass(slots=True)
class TrainingService:
    palam_curve: PalamCurve | None = None
    rng: random.Random = field(default_factory=random.Random)

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

        Called after SettlementService.settle_actor has flushed SOURCE -> PALAM.
        """
        results: list[TrainingResult] = []
        spirit = actor.stats.base.get("spirit")
        orgasm_count = 0

        counter = self._detect_counter(actor)

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
            counter=counter,
        )

    def add_development(self, actor: CharacterState, key: str, delta: int) -> int:
        return actor.add_condition(f"train_{key}", delta)

    def _detect_counter(self, actor: CharacterState) -> TrainingResult | None:
        lust = actor.stats.palam.get("lust")
        obedience = actor.stats.palam.get("obedience")
        if obedience < _COUNTER_OBEDIENCE_THRESHOLD or lust < _COUNTER_LUST_THRESHOLD:
            return None

        pleasure_total = sum(
            actor.stats.palam.get(k) for k in _PLEASURE_ORGASM_MAP
        )
        if pleasure_total < _COUNTER_PLEASURE_TOTAL:
            return None

        deterministic = self._deterministic_counter(actor, obedience)
        if deterministic is not None:
            return deterministic

        return self._probabilistic_counter(actor, lust, obedience)

    def _deterministic_counter(
        self, actor: CharacterState, obedience: int
    ) -> TrainingResult | None:
        abl_service = actor.stats.compat.abl.get(13)
        abl_lust = actor.stats.compat.abl.get(11)
        abl_intimacy = actor.stats.compat.abl.get(9)

        if abl_service >= 3 and obedience >= 1000:
            return TrainingResult.COUNTER_SERVICE
        if abl_intimacy >= 3:
            return TrainingResult.COUNTER_KISS
        if abl_lust >= 2:
            return TrainingResult.COUNTER_EMBRACE
        return None

    def _probabilistic_counter(
        self, actor: CharacterState, lust: int, obedience: int
    ) -> TrainingResult | None:
        submission = actor.stats.palam.get("submission")
        rank = actor.relationship_stage.rank if actor.relationship_stage else 0
        has_pleasure_mark = actor.has_mark("pleasure_mark", 2)
        has_submission_mark = actor.has_mark("submission_mark", 3)

        chance = 0.0
        if lust >= _COUNTER_LUST_KISS:
            chance += _COUNTER_PROB_LUST_LOW
        if lust >= _COUNTER_LUST_TOUCH:
            chance += _COUNTER_PROB_LUST_HIGH
        if submission >= 3000:
            chance += _COUNTER_PROB_SUBMISSION
        if obedience >= 2000:
            chance += _COUNTER_PROB_OBEDIENCE
        if rank >= _COUNTER_RANK_LIKE:
            chance += _COUNTER_PROB_RANK_LIKE
        if has_pleasure_mark:
            chance += _COUNTER_PROB_MARK_PLEASURE
        if has_submission_mark:
            chance += _COUNTER_PROB_MARK_SUBMISSION

        chance = min(chance, _COUNTER_PROB_CAP)
        if chance <= 0.0 or self.rng.random() >= chance:
            return None

        if obedience >= _COUNTER_OBEDIENCE_SERVICE and submission >= _COUNTER_SUBMISSION_SERVICE:
            return TrainingResult.COUNTER_SERVICE
        if has_submission_mark or submission >= _COUNTER_SUBMISSION_REQUEST:
            return TrainingResult.COUNTER_REQUEST
        if lust >= _COUNTER_LUST_TOUCH:
            return TrainingResult.COUNTER_EMBRACE
        if lust >= _COUNTER_LUST_KISS and rank >= _COUNTER_RANK_LIKE:
            return TrainingResult.COUNTER_KISS
        return None
