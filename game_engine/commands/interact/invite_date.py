from __future__ import annotations

from typing import TYPE_CHECKING

from game_engine.commands._common import favor_trust_proc, global_can, new_source, get_attitude, add_attitude_mes, \
    source_proc
from game_engine.commands._common import say_chara_line
from game_engine.data_pipeline.common_src_modify import common_src_modify
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
    # 当日已约会
    if npc.cflag["have_dated_today"]:
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
    # 好感度低于400
    if npc.favor < 400:
        return False

    return True


def able(world: World, npc: ShipGirl) -> tuple[bool, str]:
    """执行成功判定
    返回 (是否成功, 明细字符串)，明细用于向玩家展示各影响因子的加减分"""
    success_score = 280
    mes, score = get_attitude(world.player, npc, 30)

    # 会话
    temp = {0: -10, 1: 0, 2: 10, 3: 20, 4: 30, 5: 40}.get(
        world.player.abl["talk_abl"], 50
    )
    score += temp
    mes = add_attitude_mes(mes, f"会话({temp})")
    # 恋人
    if npc.has_talent("lover"):
        score += 60
        mes = add_attitude_mes(mes, f"恋人(60)")

    if score >= success_score:
        mes += f"={score}≥{success_score} 成功！"
        ok = True
    else:
        mes += f"={score}<{success_score} 失败！"
        ok = False
    return ok, mes


@register_cmd("invite_date", "约会", "日常", can=can)
def invite_date(world: World, option: str):
    """约会
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    ctx.say(f'尝试邀请{npc.name}去约会……')

    ok, detail = able(world, npc)
    ctx.say(detail)
    say_chara_line(npc, ctx, 'invite_date')

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
        world.player.cflag["dating"] = True
        npc.cflag['dating_day'] = world.time_manager.day
        npc.cflag["dating_following"] = True
        npc.cflag['have_dated_today'] = True

    # 通用source修正
    source = common_src_modify(source, npc)

    ctx.say_source(source)

    # source转换过程统一处理
    source_proc(source, world.player, npc, ctx)

    # 体力和气力消耗
    energy_cost = 100
    ctx.consume(energy=energy_cost, chara=world.player)

    # 好感和信赖
    favor_trust_proc(source, npc, ctx)

    return ctx.result()
