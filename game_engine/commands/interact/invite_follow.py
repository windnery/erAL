from __future__ import annotations

from typing import TYPE_CHECKING

from game_engine.commands._common import global_can, get_attitude, add_attitude_mes
from game_engine.commands._common import say_chara_line
from ...models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World

from .._commands import register_cmd
from .._context import CommandContext


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 睡眠中
    if npc.is_sleeping():
        return False
    # 工作中
    if npc.is_working():
        return False
    # 同行中
    if npc.is_following():
        return False
    # 关系未达到友好
    if npc.get_talent_value("relationship") < 1:
        return False
    # 亲密度不足4
    if npc.abl["intimacy_abl"] < 4:
        return False
    # 好感度低于300
    if npc.favor < 300:
        return False

    return True


def able(world: World, npc: ShipGirl) -> tuple[bool, str]:
    """执行成功判定
    返回 (是否成功, 明细字符串)，明细用于向玩家展示各影响因子的加减分"""
    success_score = 180
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


@register_cmd("invite_follow", "邀请同行", "日常", can=can)
def invite_follow(world: World, option: str):
    """邀请同行
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    ctx.say(f'尝试邀请{npc.name}同行……')

    ok, detail = able(world, npc)
    ctx.say(detail)
    say_chara_line(npc, ctx, 'invite_follow')

    if not ok:
        ctx.say(f"{npc.name}拒绝了你的要求")
    else:
        ctx.say(f"{npc.name}开始跟着{world.player.name}了")
        # 进入同行状态
        npc.cflag["following"] = True

    return ctx.result()
