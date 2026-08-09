from __future__ import annotations

from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from game_engine.commands._common import favor_trust_proc, global_can, new_source
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.palam.palam_calc import palam_calc

from ...models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World

from .._commands import register_cmd
from .._context import CommandContext


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 通用判定
    if not global_can(world.player, npc):
        return False
    # 工作中
    if npc.is_working():
        return False
    # 约会中
    if npc.is_dating():
        return False
    # 关系未达到友好
    if npc.get_talent_value("relationship") < 1:
        return False
    # 亲密度不足5
    if npc.abl["intimacy_abl"] < 5:
        return False
    # 好感度低于240
    return not npc.favor < 240


def able(world: World, npc: ShipGirl) -> tuple[bool, str]:
    """执行成功判定
    返回 (是否成功, 明细字符串)，明细用于向玩家展示各影响因子的加减分"""
    SUCCESS_SCORE = 24
    score = 0
    # 记录各影响因子 (名称, 增量)
    parts: list[tuple[str, int]] = []
    _add = parts.append

    # 好感度
    if npc.favor < 300:
        score -= 1
        _add(("好感度", -1))
    elif npc.favor < 500:
        score += 2
        _add(("好感度", 2))
    elif npc.favor < 700:
        score += 3
        _add(("好感度", 3))
    elif npc.favor < 900:
        score += 4
        _add(("好感度", 4))
    else:
        score += 6
        _add(("好感度", 6))
    # 亲密
    intimacy_delta = {6: 2, 7: 3, 8: 5, 9: 6}.get(npc.abl["intimacy_abl"], 7)
    score += intimacy_delta
    _add(("亲密", intimacy_delta))
    # 顺从
    obedience_delta = {0: -2, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5}.get(
        npc.abl["obedience_abl"], 6
    )
    score += obedience_delta
    _add(("顺从", obedience_delta))
    # 侍奉精神
    servant_delta = {0: 0, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5}.get(npc.abl["servant_abl"], 6)
    score += servant_delta
    _add(("侍奉精神", servant_delta))
    # 会话
    talk_delta = {0: -1, 1: 1, 2: 2, 3: 3, 4: 4, 5: 5}.get(
        world.player.abl["talk_abl"], 6
    )
    score += talk_delta
    _add(("会话", talk_delta))
    # 秘书舰
    if npc == world.npc_manager.secretary_ship:
        score += 4
        _add(("秘书舰", 4))
    # 陷落阶段
    relationship = npc.get_talent_value("relationship")
    rel_delta = relationship * 3
    score += rel_delta
    _add(("陷落阶段", rel_delta))
    # 恋人
    if npc.has_talent("lover"):
        score += 8
        _add(("恋人", 8))
    # 胆怯
    if npc.get_talent_value("courage") == -1:
        score -= 2
        _add(("胆怯", -2))
    # 叛逆
    if npc.get_talent_value("attitude") == 1:
        score -= 4
        _add(("叛逆", -4))
    # 傲慢
    if npc.get_talent_value("response") == 1:
        score -= 2
        _add(("傲慢", -2))
    # 自尊心高
    if npc.get_talent_value("self_respect") == 1:
        score -= 1
        _add(("自尊心高", -1))
    # 傲娇
    if npc.has_talent("tsundere"):
        # 傲娇且关系在喜欢以下
        if npc.get_talent_value("relationship") < 2:
            score -= 2
            _add(("傲娇", -2))
        else:
            score += 3
            _add(("傲娇", 3))
    # 冷漠
    if npc.has_talent("indifference"):
        score -= 3
        _add(("冷漠", -3))
    # 感情缺乏
    if npc.has_talent("emotional_deficiency"):
        score -= 3
        _add(("感情缺乏", -3))
    # 开朗的
    if npc.has_talent("bright"):
        score += 2
        _add(("开朗的", 2))
    # 阴郁的
    if npc.has_talent("morose"):
        score -= 2
        _add(("阴郁的", -2))
    # 难以逾越的底线
    if npc.has_talent("impassable_line") and npc.exp["love_exp"] == 0:
        score -= 5
        _add(("难以逾越的底线", -5))
    # 不在意目光
    if npc.has_talent("not_minding_the_gaze"):
        score += 1
        _add(("不在意目光", 1))
    # 自己爱解放
    self_love_delta = npc.get_talent_value("self_love") * 2
    score += self_love_delta
    _add(("自己爱解放", self_love_delta))
    # 抵抗
    if npc.has_talent("resistance"):
        score -= 3
        _add(("抵抗", -3))
    # 羞耻心(-1不知羞耻 1害羞)
    shame_delta = -npc.get_talent_value("shame") * 2
    score += shame_delta
    _add(("羞耻心", shame_delta))
    # 献身的
    if npc.has_talent("devoted"):
        score += 3
        _add(("献身的", 3))
    # 玩家魅力
    charm_delta = world.player.get_talent_value("charm") * 2
    score += charm_delta
    _add(("玩家魅力", charm_delta))

    # 生成明细：跳过增量为 0 的因子
    detail = "+".join(f"{name}({delta})" for name, delta in parts if delta != 0)
    if score >= SUCCESS_SCORE:
        detail += f"={score}≥{SUCCESS_SCORE} 成功！"
        ok = True
    else:
        detail += f"={score}<{SUCCESS_SCORE} 失败！"
        ok = False
    return ok, detail


@register_cmd("invite_date", "约会", "日常", can)
def invite_date(world: World, option: str):
    """约会
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)

    line = npc.get_line("invite_date")
    ctx.say(f"尝试邀请{npc.name}去约会……")
    if line:
        # 有口上
        ctx.say(line.replace("{name}", npc.name))

    ok, detail = able(world, npc)
    ctx.say(detail)
    if not ok:
        ctx.say(f"{npc.name}拒绝了你的邀请")
        source: dict[str, int] = new_source(
            {"escape_source": 200, "disgust_source": 400}
        )
    else:
        ctx.say(f"{npc.name}接受了你的邀请！")
        source: dict[str, int] = new_source(
            {
                "love_source": 200,
                "achievement_source": 100,
                "lust_source": 100,
                "obedience_source": 100,
                "happiness_source": 200,
            }
        )
        # 进入约会状态
        npc.cflag["dating"] = True
        npc.cflag["dating_following"] = True

    # 通用source修正
    source = common_src_modify(source, npc)
    source_list = []
    for k, v in source.items():
        if v != 0:
            source_list.append(f"{ATTR_DEFS['source'][k]['name']}({v})")
    ctx.say(" ".join(source_list))
    # source->palam
    mes_source, mes_target = palam_calc(source, world.player, npc)
    for mes in mes_source:
        ctx.say(mes)
    for mes in mes_target:
        ctx.say(mes)
    # 更新palam等级
    world.player.update_palam_level()
    npc.update_palam_level()
    # 体力和气力消耗
    energy_cost = 100
    ctx.consume(energy=energy_cost, chara=world.player)
    # 好感和信赖
    favor_trust_proc(source, npc, ctx)

    return ctx.result()
