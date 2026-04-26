"""SOURCE_EXTRA 执行器：全局 TALENT 倍率修饰 + 训练印记快感倍率。"""

from __future__ import annotations

from eral.content.source_extra import SourceExtraCondition, SourceExtraModifier
from eral.domain.stats import ActorNumericState
from eral.domain.world import CharacterState


# 快感类 SOURCE 索引（0=快C, 1=快V, 2=快A, 3=快B, 4=快M）
_PLEASURE_KEYS = ("0", "1", "2", "3", "4")

# 快感印记 → SOURCE 倍率
_MARK_SOURCE_MULTIPLIERS = {
    "pleasure_mark": {
        1: 1.2,
        2: 1.5,
        3: 2.0,
    },
}

# 苦痛印记 → 各 SOURCE 倍率
# 格式：印记等级 -> ( {source索引: 倍率, ...}, 预留 )
_MARK_PAIN_MULTIPLIERS = {
    "pain_mark": {
        1: ({"14": 1.2}, {}),          # 恐惧 ×1.2
        2: ({"14": 1.5, "16": 1.2}, {}),  # 恐惧×1.5, 恭顺×1.2
        3: ({"14": 2.0, "16": 1.5}, {}),  # 恐惧×2.0, 恭顺×1.5
    },
}


def apply_source_extra(
    stats: ActorNumericState,
    modifiers: tuple[SourceExtraModifier, ...],
) -> dict[str, float]:
    """应用 SOURCE_EXTRA 修饰器到 stats.source，返回实际应用的倍率字典。"""

    applied: dict[str, float] = {}

    for modifier in modifiers:
        for source_key in modifier.target_sources:
            current = stats.source.get(source_key)
            if current == 0:
                continue

            total_mult = 1.0
            for condition in modifier.conditions:
                mult = _eval_condition(stats, condition)
                if mult != 1.0:
                    total_mult *= mult

            if total_mult == 1.0:
                continue

            if modifier.operation == "multiply":
                new_val = int(current * total_mult)
                stats.source.set(source_key, new_val)
                applied[source_key] = applied.get(source_key, 1.0) * total_mult
            elif modifier.operation == "add":
                bonus = int(total_mult)
                if bonus != 0:
                    stats.source.add(source_key, bonus)
                    applied[source_key] = applied.get(source_key, 0.0) + bonus

    return applied


def _eval_condition(stats: ActorNumericState, condition: SourceExtraCondition) -> float:
    """评估一个 SOURCE_EXTRA 条件。返回倍率（1.0 = 无效果）。"""

    if condition.kind == "talent_value":
        v = stats.compat.talent.get(condition.talent_index)
        if condition.base == 0:
            return 1.0
        return (condition.base + condition.coeff * v) / condition.base

    if condition.kind == "talent_present":
        v = stats.compat.talent.get(condition.talent_index)
        if v > 0:
            return condition.multiplier
        return 1.0

    if condition.kind == "talent_level":
        v = stats.compat.talent.get(condition.talent_index)
        for lvl, mult in condition.levels:
            if v == lvl:
                return mult
        return 1.0

    return 1.0


def compute_recovery_modifier(stats: ActorNumericState) -> float:
    """从 TALENT 计算恢复速度修正。

    eraTW: 回復速度 (talent_index 130)。
    """
    recovery_speed = stats.compat.talent.get(130)
    # 0=慢, 1=快。基础恢复乘以 (10 + speed * 5) / 10
    return (10.0 + recovery_speed * 5.0) / 10.0


def compute_aptitude_offset(stats: ActorNumericState) -> int:
    """从 TALENT 计算 ABL 升级天赋偏移。

    eraTW: 快感应答 (talent_index 70) 加速 ABL 成长。
    """
    return stats.compat.talent.get(70)


def apply_training_mark_effects(actor: CharacterState) -> dict[str, float]:
    """应用训练印记的 SOURCE 倍率。返回实际应用的倍率字典。"""
    applied: dict[str, float] = {}

    pleasure_level = actor.marks.get("pleasure_mark", 0)
    if pleasure_level > 0:
        mult = _MARK_SOURCE_MULTIPLIERS["pleasure_mark"].get(pleasure_level, 1.0)
        for key in _PLEASURE_KEYS:
            current = actor.stats.source.get(key)
            if current > 0:
                actor.stats.source.set(key, int(current * mult))
                applied[key] = applied.get(key, 1.0) * mult

    pain_level = actor.marks.get("pain_mark", 0)
    if pain_level > 0:
        entry = _MARK_PAIN_MULTIPLIERS["pain_mark"].get(pain_level)
        if entry:
            for source_key, mult in entry[0].items():
                current = actor.stats.source.get(source_key)
                if current > 0:
                    actor.stats.source.set(source_key, int(current * mult))
                    applied[source_key] = applied.get(source_key, 1.0) * mult

    return applied
