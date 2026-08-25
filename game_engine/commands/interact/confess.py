from __future__ import annotations

from typing import TYPE_CHECKING

from game_engine.commands._common import favor_trust_proc, global_can, new_source, get_attitude, add_attitude_mes, \
    source_proc
from game_engine.commands._common import say_chara_line
from game_engine.data_pipeline.common_src_modify import common_src_modify
from .._commands import register_cmd
from .._context import CommandContext
from ...models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 通用判定(气力0 睡眠)
    if not global_can(world.player, npc):
        return False
    # 工作中
    if npc.is_working():
        return False
    # 已经是恋人了
    if npc.has_talent('lover'):
        return False
    # 关系未达到喜欢
    if npc.get_talent_value("relationship") < 2:
        return False
    # 亲密度不足7
    if npc.abl["intimacy_abl"] < 7:
        return False
    # 好感度低于800
    if npc.favor < 800:
        return False

    return True


def able(world: World, npc: ShipGirl) -> tuple[bool, str]:
    """执行成功判定
    返回 (是否成功, 明细字符串)，明细用于向玩家展示各影响因子的加减分"""
    success_score = 350
    mes, score = get_attitude(world.player, npc, 100)

    # 会话
    temp = {0: -10, 1: 0, 2: 10, 3: 20, 4: 30, 5: 40}.get(
        world.player.abl["talk_abl"], 50
    )
    score += temp
    mes = add_attitude_mes(mes, f"会话({temp})")

    if score >= success_score:
        mes += f"={score}≥{success_score} 成功！"
        ok = True
    else:
        mes += f"={score}<{success_score} 失败！"
        ok = False
    return ok, mes


@register_cmd("confess", "告白", "日常", can=can)
def confess(world: World, option: str):
    """告白
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    ctx.say(f'鼓起勇气对{npc.name}告白了！')

    ok, detail = able(world, npc)
    ctx.say(detail)
    say_chara_line(npc, ctx, 'confess')

    if not ok:
        ctx.say(f"尽管很诚心地告白了，但还是被{npc.name}拒绝了……")
        source: dict[str, int] = new_source(
            {"escape_source": 400, "disgust_source": 800}
        )
    else:
        ctx.say(f"{npc.name}接受了你的告白！")
        ctx.say(f"现在开始{world.player.name}和{npc.name}成为[[c:#ff6fae]][恋人][[/c]]了！")
        source: dict[str, int] = new_source(
            {
                "love_source": 800,
                "achievement_source": 400,
                "lust_source": 200,
                "obedience_source": 400,
                "happiness_source": 800,
            }
        )
        # talent: 恋人
        npc.set_talent("lover", 1)

    # 通用source修正
    source = common_src_modify(source, npc)
    ctx.say_source(source, prefix=npc.name)

    # source转换过程统一处理
    source_proc(source, world.player, npc, ctx)

    # 体力和气力消耗
    energy_cost = 100
    ctx.consume(energy=energy_cost, chara=world.player)

    # 好感和信赖
    favor_trust_proc(source, npc, ctx)

    return ctx.result()
