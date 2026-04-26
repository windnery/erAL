"""结算管线：CUP/CDOWN 中间层 + FAVOR/TRUST 计算 + SOURCE_EXTRA 全局修饰。"""

from __future__ import annotations

from dataclasses import dataclass, field

from eral.content.abl_upgrade import AblUpgradeConfig
from eral.content.palamlv import PalamToJuelRule
from eral.content.settlement import SettlementRule
from eral.content.source_extra import SourceExtraModifier
from eral.content.source_modifiers import SourceCbvaRule
from eral.content.stat_axes import AxisFamily
from eral.domain.actions import AppliedChange, CupBoard
from eral.domain.world import CharacterState, WorldState
from eral.systems.facilities import FacilityService
from eral.systems.favor_calc import GrowthFormula, compute_favor_delta, compute_trust_delta
from eral.systems.imprint import ImprintService
from eral.systems.relationships import RelationshipService
from eral.systems.source_extra import apply_source_extra, apply_training_mark_effects
from eral.systems.source_modifiers import apply_source_modifiers


CFLAG_AFFECTION = 2
CFLAG_TRUST = 4


@dataclass(slots=True)
class SettlementService:
    """将 SOURCE 值经过 CUP/CDOWN 管线结算为 PALAM/CFLAG 最终值。"""

    rules: tuple[SettlementRule, ...]
    palam_to_juel_rules: tuple[PalamToJuelRule, ...] = ()
    source_modifiers: dict[int, SourceCbvaRule] = field(default_factory=dict)
    source_extra_modifiers: tuple[SourceExtraModifier, ...] = ()
    relationship_service: RelationshipService | None = None
    imprint_check: ImprintService | None = None
    mark_max_levels: dict[str, int] | None = None
    favor_formula: GrowthFormula | None = None
    trust_formula: GrowthFormula | None = None
    abl_upgrade_config: AblUpgradeConfig | None = None
    facility_service: FacilityService | None = None

    def settle_actor(self, world: WorldState, actor: CharacterState) -> list[AppliedChange]:
        """执行一个角色的完整结算管线。

        Phase -1: SOURCE_EXTRA — 全局天赋/状态修饰器（修改 SOURCE 本身）
        Phase 0:  SOURCE_CBVA  — 逐个轴处理 SOURCE → CUP
        Phase 1:  CUP → CUP/CDOWN 分流 + 直接 CFLAG
        Phase 1.5: FAVOR_CALC / TRUST_CALC → CFLAG 好感/信赖
        Phase 2:  PALAM += CUP - CDOWN
        Phase 2.5: PALAM → JUEL 转换
        Phase 3:  Imprint 检查
        Phase 4:  同步派生字段，清空缓冲区
        """
        changes: list[AppliedChange] = []
        board = CupBoard()

        # Phase -1: SOURCE_EXTRA — 全局修饰（先于 CBVA）
        apply_source_extra(actor.stats, self.source_extra_modifiers)
        apply_training_mark_effects(actor)

        # Phase 0: SOURCE → CUP（应用 CBVA 修饰因子；无规则的索引原样复制）
        apply_source_modifiers(actor, self.source_modifiers)

        for rule in self.rules:
            cup_value = actor.stats.cup.get(rule.cup_index)
            if cup_value == 0:
                continue

            delta = int(cup_value * rule.scale)
            target_family = rule.target_family
            target_key = str(rule.target_index)

            if target_family == AxisFamily.PALAM:
                if delta > 0:
                    board.add_cup(target_key, delta)
                else:
                    board.add_cdown(target_key, abs(delta))
            elif target_family == AxisFamily.CFLAG:
                before = actor.get_cflag(rule.target_index)
                after = actor.add_cflag(rule.target_index, delta)
                changes.append(
                    AppliedChange("cflag", target_key, before, after, delta)
                )
            elif target_family in {AxisFamily.TFLAG, AxisFamily.FLAG}:
                condition_key = f"{target_family.value}_{rule.target_index}"
                before = world.get_condition(condition_key)
                after = world.add_condition(condition_key, delta)
                changes.append(
                    AppliedChange("condition", condition_key, before, after, delta)
                )

        # Phase 1.5: FAVOR_CALC / TRUST_CALC（好感/信赖度变化）
        stage_key = actor.relationship_stage.key if actor.relationship_stage else "stranger"
        if self.favor_formula is not None:
            favor_delta = compute_favor_delta(actor.stats, stage_key, self.favor_formula)
            if self.facility_service is not None and favor_delta > 0:
                favor_delta = int(favor_delta * self.facility_service.relation_multiplier(world))
            if favor_delta > 0:
                before = actor.get_cflag(CFLAG_AFFECTION)
                after = actor.add_cflag(CFLAG_AFFECTION, favor_delta)
                changes.append(AppliedChange("cflag", str(CFLAG_AFFECTION), before, after, favor_delta))
        if self.trust_formula is not None:
            trust_delta = compute_trust_delta(actor.stats, stage_key, self.trust_formula)
            if self.facility_service is not None and trust_delta > 0:
                trust_delta = int(trust_delta * self.facility_service.relation_multiplier(world))
            if trust_delta > 0:
                before = actor.get_cflag(CFLAG_TRUST)
                after = actor.add_cflag(CFLAG_TRUST, trust_delta)
                changes.append(AppliedChange("cflag", str(CFLAG_TRUST), before, after, trust_delta))

        # Phase 2: Apply CUP/CDOWN to PALAM
        palam_increments: dict[str, int] = {}
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
            if net > 0:
                palam_increments[key] = net

        # Phase 2.5: PALAM → JUEL conversion
        for rule in self.palam_to_juel_rules:
            palam_key = str(rule.palam_index)
            increment = palam_increments.get(palam_key, 0)
            if increment <= 0:
                continue
            juel_gain = increment // rule.divisor
            if juel_gain <= 0:
                continue
            juel_key = str(rule.juel_index)
            before = actor.stats.juel.get(juel_key)
            after = actor.stats.juel.add(juel_key, juel_gain)
            changes.append(AppliedChange("juel", juel_key, before, after, juel_gain))

        # Phase 3: Imprint check
        if self.imprint_check is not None and self.mark_max_levels is not None:
            self.imprint_check.check_and_apply(actor, board, self.mark_max_levels)

        # Phase 4: Sync and clear
        actor.sync_derived_fields()
        if self.relationship_service is not None:
            self.relationship_service.update_actor(actor)
        actor.stats.clear_source()
        actor.stats.clear_cup()
        board.clear()
        return changes

    def apply_abl_upgrades(self, actor: CharacterState) -> list[tuple[int, int, int]]:
        """Run ABL upgrade check (called after sleep / day-end)."""
        if self.abl_upgrade_config is None:
            return []
        from eral.systems.abl_upgrade import check_and_apply_abl_upgrades
        from eral.systems.source_extra import compute_aptitude_offset

        aptitude_offset = compute_aptitude_offset(actor.stats)
        return check_and_apply_abl_upgrades(
            actor.stats, self.abl_upgrade_config, aptitude_offset,
        )
