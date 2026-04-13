"""Imprint (刻印) triggering service.

Checks CUP accumulation against imprint thresholds after settlement,
and automatically upgrades mark levels when thresholds are exceeded.
"""

from __future__ import annotations

from eral.content.imprint import ImprintThreshold
from eral.domain.actions import CupBoard
from eral.domain.world import CharacterState


class ImprintService:
    """Check and apply imprint marks based on CUP/SOURCE accumulation."""

    def __init__(self, thresholds: tuple[ImprintThreshold, ...]) -> None:
        self.thresholds = thresholds

    def check_and_apply(
        self,
        actor: CharacterState,
        board: CupBoard,
        mark_max_levels: dict[str, int],
    ) -> list[str]:
        """Check CUP/SOURCE values against thresholds and apply imprint upgrades.

        Returns list of imprint keys that were upgraded.
        """
        applied: list[str] = []

        for threshold in self.thresholds:
            cup_value = self._accumulate_value(actor, board, threshold)
            if cup_value <= 0:
                continue

            current_level = actor.marks.get(threshold.key, 0)
            max_level = mark_max_levels.get(threshold.key, 3)

            new_level = current_level
            if cup_value >= threshold.lv3_threshold:
                new_level = max(new_level, 3)
            elif cup_value >= threshold.lv2_threshold:
                new_level = max(new_level, 2)
            elif cup_value >= threshold.lv1_threshold:
                new_level = max(new_level, 1)

            if new_level > current_level and new_level <= max_level:
                actor.set_mark(threshold.key, new_level, max_level=max_level)
                applied.append(threshold.key)

        return applied

    def _accumulate_value(
        self,
        actor: CharacterState,
        board: CupBoard,
        threshold: ImprintThreshold,
    ) -> int:
        """Sum CUP value from PALAM key and/or SOURCE keys for this threshold."""
        total = 0

        if threshold.palam_key:
            total += board.cup.get(threshold.palam_key, 0)

        for source_key in threshold.source_keys:
            total += actor.stats.source.get(source_key)

        return total