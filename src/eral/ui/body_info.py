"""Derive body-part development tags and milestone entries for the status panel.

Pure helpers over CharacterState — no world or service dependency.
"""

from __future__ import annotations

from dataclasses import dataclass

from eral.domain.world import CharacterState


@dataclass(frozen=True, slots=True)
class BodyPartInfo:
    label: str
    tags: tuple[str, ...]          # development labels like "未开发", "笨拙"
    description: str               # one-line state descriptor
    history: str = ""              # optional milestone line


_DEV_LABELS_PLEASURE = (
    (12000, "完熟"),
    (6000, "开花"),
    (3000, "开发中"),
    (0, "未开发"),
)

_DEV_LABELS_ABL = (
    (5, "熟练"),
    (3, "经验尚浅"),
    (1, "笨拙"),
    (0, "完全不懂"),
)


def _pleasure_label(value: int) -> str:
    for threshold, label in _DEV_LABELS_PLEASURE:
        if value >= threshold:
            return label
    return "未开发"


def _abl_label(value: int) -> str:
    for threshold, label in _DEV_LABELS_ABL:
        if value >= threshold:
            return label
    return "完全不懂"


def _body_general(actor: CharacterState) -> BodyPartInfo:
    """身 — general body sensitivity."""
    lubrication = actor.stats.palam.get("lubrication")
    if lubrication >= 3000:
        desc = "这副身体很容易湿"
    elif lubrication >= 1000:
        desc = "这副身体开始熟悉被爱抚的感觉"
    else:
        desc = "这副身体不太容易湿"
    return BodyPartInfo(label="身", tags=(), description=desc)


def _finger(actor: CharacterState) -> BodyPartInfo:
    abl = actor.stats.compat.abl.get(13)  # 奉仕
    tags = (_abl_label(abl),)
    if abl >= 3:
        desc = "手指动作已经熟练"
    elif abl >= 1:
        desc = "手的动作还需要多学习"
    else:
        desc = "手…不是这样弄的"
    return BodyPartInfo(label="指", tags=tags, description=desc)


def _chest(actor: CharacterState) -> BodyPartInfo:
    pleasure_c = actor.stats.palam.get("0")
    afterglow = actor.stats.base.get("pleasure_c_afterglow")
    tags = (_pleasure_label(pleasure_c),)
    if tags[0] == "未开发" and afterglow == 0:
        desc = "【笨拙】胸部？该…怎样做呢？"
    elif pleasure_c < 3000:
        desc = "没什么特别的感觉"
    elif pleasure_c < 6000:
        desc = "胸部开始敏感了"
    else:
        desc = "胸部变得很敏感"
    return BodyPartInfo(label="胸", tags=tags, description=desc)


def _clit(actor: CharacterState) -> BodyPartInfo:
    pleasure_c = actor.stats.palam.get("0")
    tags = (_pleasure_label(pleasure_c),)
    if pleasure_c < 3000:
        desc = "即便被爱抚也没什么特别的感觉"
    elif pleasure_c < 6000:
        desc = "被爱抚时会有些反应"
    else:
        desc = "被爱抚时会产生强烈的快感"
    return BodyPartInfo(label="阴蒂", tags=tags, description=desc)


def _mouth(actor: CharacterState) -> BodyPartInfo:
    pleasure_m = actor.stats.palam.get("4")
    abl_oral = actor.stats.compat.abl.get(13)
    tags = (_abl_label(abl_oral), _pleasure_label(pleasure_m))
    has_first_kiss = actor.memories.get("milestone:first_kiss", 0) > 0
    kiss_day = actor.get_condition("milestone:first_kiss_day")
    if has_first_kiss and kiss_day:
        history = f"初吻履历：第 {kiss_day} 日被夺去"
    else:
        history = "初吻履历：还保有初吻"
    if pleasure_m < 3000:
        desc = "【未开发】即便被爱抚也没什么特别的感觉"
    elif pleasure_m < 6000:
        desc = "口腔逐渐被开发"
    else:
        desc = "唇舌都已熟知快感"
    return BodyPartInfo(label="口", tags=tags, description=desc, history=history)


def _anal(actor: CharacterState) -> BodyPartInfo:
    pleasure_a = actor.stats.palam.get("2")
    tags: tuple[str, ...]
    first_anal = actor.memories.get("milestone:first_sex", 0) > 0 and actor.get_condition("anal_first_day") > 0
    anal_day = actor.get_condition("anal_first_day")
    if anal_day:
        history = f"肛门处女丧失履历：第 {anal_day} 日"
        tags = ("已开通", _pleasure_label(pleasure_a))
    else:
        history = "肛门处女丧失履历：还没被使用过"
        tags = ("未开通", _pleasure_label(pleasure_a))
    if pleasure_a < 3000:
        desc = "【未开发】即便被爱抚也没什么特别的感觉"
    elif pleasure_a < 6000:
        desc = "后面的感觉越来越清晰"
    else:
        desc = "对后面的刺激已经很敏感"
    return BodyPartInfo(label="肛", tags=tags, description=desc, history=history)


def _vagina(actor: CharacterState) -> BodyPartInfo:
    pleasure_v = actor.stats.palam.get("1")
    virginity_day = actor.get_condition("virginity_lost_day")
    tags: tuple[str, ...]
    if virginity_day:
        history = f"处女丧失履历：第 {virginity_day} 日"
        tags = ("已开通", _pleasure_label(pleasure_v))
    else:
        history = "处女丧失履历：还没被任何人进入"
        tags = ("处女", _pleasure_label(pleasure_v))
    if pleasure_v < 3000:
        desc = "【未开发】还产生不了什么特别的感觉"
    elif pleasure_v < 6000:
        desc = "身体开始记住被填满的感觉"
    else:
        desc = "每次进入都会产生强烈快感"
    return BodyPartInfo(label="膣", tags=tags, description=desc, history=history)


def _uterus(actor: CharacterState) -> BodyPartInfo:
    inside = actor.memories.get("evt:player_ejaculation_inside", 0)
    if inside == 0:
        desc = "子宫还未被玩家的精液抵达"
    elif inside < 5:
        desc = "开始记住被注入的感觉"
    else:
        desc = "已经习惯被玩家的精液充满"
    tags: tuple[str, ...] = ("无感应",) if inside == 0 else ("被调教",)
    return BodyPartInfo(label="子宫", tags=tags, description=desc)


def outer_parts(actor: CharacterState) -> tuple[BodyPartInfo, ...]:
    return (
        _body_general(actor),
        _finger(actor),
        _chest(actor),
        _clit(actor),
    )


def inner_parts(actor: CharacterState) -> tuple[BodyPartInfo, ...]:
    return (
        _mouth(actor),
        _anal(actor),
        _vagina(actor),
        _uterus(actor),
    )
