"""Settlement pipeline with CUP/CDOWN intermediate layer."""

from __future__ import annotations

from dataclasses import dataclass, field

from eral.content.settlement import SettlementRule
from eral.content.stat_axes import AxisFamily
from eral.domain.actions import AppliedChange, CupBoard
from eral.domain.world import CharacterState, WorldState
from eral.systems.relationships import RelationshipService


@dataclass(slots=True)
class SettlementService:
    """Apply SOURCE values through the CUP/CDOWN pipeline."""

    rules: tuple[SettlementRule, ...]
    relationship_service: RelationshipService | None = None
    imprint_check: object | None = None
    mark_max_levels: dict[str, int] | None = None

    def settle_actor(self, world: WorldState, actor: CharacterState) -> list[AppliedChange]:
        """Execute full settlement pipeline for one actor.

        Phase 1: SOURCE → CUP/CDOWN split
        Phase 2: Direct CFLAG/BASE writes
        Phase 3: PALAM += CUP - CDOWN
        Phase 4: Sync derived fields, clear buffers
        """
        changes: list[AppliedChange] = []
        board = CupBoard()

        # Phase 1+2: Apply rules, routing PALAM targets through CUP/CDOWN
        #            and CFLAG/BASE targets directly
        for rule in self.rules:
            source_value = actor.stats.source.get(rule.source)
            if source_value == 0:
                continue

            delta = source_value * rule.scale
            target_family = rule.target_family

            if target_family == AxisFamily.PALAM and rule.target_key:
                # PALAM targets go through CUP/CDOWN buffer
                if delta > 0:
                    board.add_cup(rule.target_key, delta)
                else:
                    board.add_cdown(rule.target_key, abs(delta))
            elif target_family == AxisFamily.BASE and rule.target_key:
                # BASE writes are direct (no CUP buffer)
                before = actor.stats.base.get(rule.target_key)
                after = actor.stats.base.add(rule.target_key, delta)
                changes.append(AppliedChange("base", rule.target_key, before, after, delta))
            elif target_family == AxisFamily.CFLAG and rule.target_index is not None:
                # CFLAG writes are direct (no CUP buffer)
                before = actor.stats.compat.cflag.get(rule.target_index)
                after = actor.stats.compat.cflag.add(rule.target_index, delta)
                changes.append(
                    AppliedChange("cflag", str(rule.target_index), before, after, delta)
                )
            elif target_family == AxisFamily.TFLAG and rule.target_index is not None:
                before = world.compat.tflag.get(rule.target_index)
                after = world.compat.tflag.add(rule.target_index, delta)
                changes.append(
                    AppliedChange("tflag", str(rule.target_index), before, after, delta)
                )

        # Phase 3: Apply CUP/CDOWN to PALAM
        all_keys = set(board.cup.keys()) | set(board.cdown.keys())
        for key in all_keys:
            cup_val = board.cup.get(key, 0)
            cdown_val = board.cdown.get(key, 0)
            net = cup_val - cdown_val
            if net == 0:
                continue
            before = actor.stats.palam.get(key)
            after = actor.stats.palam.add(key, net)
            changes.append(AppliedChange("palam", key, before, after, net))

        # Phase 4: Imprint check (刻印判定)
        if self.imprint_check is not None and self.mark_max_levels is not None:
            self.imprint_check.check_and_apply(actor, board, self.mark_max_levels)

        # Phase 5: Sync and clear
        actor.sync_derived_fields()
        if self.relationship_service is not None:
            self.relationship_service.update_actor(actor)
        actor.stats.clear_source()
        board.clear()
        return changes