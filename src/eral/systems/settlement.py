"""Settlement pipeline with CUP/CDOWN intermediate layer and FAVOR/TRUST calculation."""

from __future__ import annotations

from dataclasses import dataclass, field

from eral.content.abl_upgrade import AblUpgradeConfig
from eral.content.settlement import SettlementRule
from eral.content.stat_axes import AxisFamily
from eral.content.talent_effects import TalentEffect
from eral.domain.actions import AppliedChange, CupBoard
from eral.domain.world import CharacterState, WorldState
from eral.systems.abl_upgrade import check_and_apply_abl_upgrades
from eral.systems.facilities import FacilityService
from eral.systems.favor_calc import GrowthFormula, compute_favor_delta, compute_trust_delta
from eral.systems.relationships import RelationshipService
from eral.systems.source_extra import compute_aptitude_offset


CFLAG_AFFECTION = 2
CFLAG_TRUST = 4


@dataclass(slots=True)
class SettlementService:
    """Apply SOURCE values through the CUP/CDOWN pipeline."""

    rules: tuple[SettlementRule, ...]
    relationship_service: RelationshipService | None = None
    imprint_check: object | None = None
    mark_max_levels: dict[str, int] | None = None
    favor_formula: GrowthFormula | None = None
    trust_formula: GrowthFormula | None = None
    abl_upgrade_config: AblUpgradeConfig | None = None
    talent_effects: tuple[TalentEffect, ...] | None = None
    facility_service: FacilityService | None = None

    def settle_actor(self, world: WorldState, actor: CharacterState) -> list[AppliedChange]:
        """Execute full settlement pipeline for one actor.

        Phase 1: SOURCE → CUP/CDOWN split + direct CFLAG/BASE
        Phase 1.5: FAVOR_CALC / TRUST_CALC → CFLAG affection/trust
        Phase 2: PALAM += CUP - CDOWN
        Phase 3: Imprint check
        Phase 3.5: ABL upgrade check
        Phase 4: Sync derived fields, clear buffers
        """
        changes: list[AppliedChange] = []
        board = CupBoard()

        for rule in self.rules:
            source_value = actor.stats.source.get(rule.source)
            if source_value == 0:
                continue

            delta = int(source_value * rule.scale)
            target_family = rule.target_family

            if target_family == AxisFamily.PALAM and rule.target_key:
                if delta > 0:
                    board.add_cup(rule.target_key, delta)
                else:
                    board.add_cdown(rule.target_key, abs(delta))
            elif target_family == AxisFamily.BASE and rule.target_key:
                before = actor.stats.base.get(rule.target_key)
                after = actor.stats.base.add(rule.target_key, delta)
                changes.append(AppliedChange("base", rule.target_key, before, after, delta))
            elif target_family == AxisFamily.CFLAG and rule.target_index is not None:
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

        # Phase 1.5: FAVOR_CALC / TRUST_CALC
        stage_key = actor.relationship_stage.key if actor.relationship_stage else "stranger"
        if self.favor_formula is not None:
            favor_delta = compute_favor_delta(actor.stats, stage_key, self.favor_formula)
            if self.facility_service is not None and favor_delta > 0:
                favor_delta = int(favor_delta * self.facility_service.relation_multiplier(world))
            if favor_delta > 0:
                before = actor.stats.compat.cflag.get(CFLAG_AFFECTION)
                after = actor.stats.compat.cflag.add(CFLAG_AFFECTION, favor_delta)
                changes.append(AppliedChange("cflag", str(CFLAG_AFFECTION), before, after, favor_delta))
        if self.trust_formula is not None:
            trust_delta = compute_trust_delta(actor.stats, stage_key, self.trust_formula)
            if self.facility_service is not None and trust_delta > 0:
                trust_delta = int(trust_delta * self.facility_service.relation_multiplier(world))
            if trust_delta > 0:
                before = actor.stats.compat.cflag.get(CFLAG_TRUST)
                after = actor.stats.compat.cflag.add(CFLAG_TRUST, trust_delta)
                changes.append(AppliedChange("cflag", str(CFLAG_TRUST), before, after, trust_delta))

        # Phase 2: Apply CUP/CDOWN to PALAM
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

        # Phase 3: Imprint check
        if self.imprint_check is not None and self.mark_max_levels is not None:
            self.imprint_check.check_and_apply(actor, board, self.mark_max_levels)

        # Phase 3.5: ABL upgrade check
        abl_upgrades: list[tuple[int, int, int]] = []
        if self.abl_upgrade_config is not None:
            aptitude_offset = 0
            if self.talent_effects is not None:
                aptitude_offset = compute_aptitude_offset(actor.stats, self.talent_effects)
            abl_upgrades = check_and_apply_abl_upgrades(
                actor.stats, self.abl_upgrade_config, aptitude_offset,
            )

        # Phase 4: Sync and clear
        actor.sync_derived_fields()
        if self.relationship_service is not None:
            self.relationship_service.update_actor(actor)
        actor.stats.clear_source()
        board.clear()
        return changes

    @property
    def last_abl_upgrades(self) -> list[tuple[int, int, int]]:
        """ABL upgrades from the most recent settle_actor call."""
        return getattr(self, "_last_abl_upgrades", [])
