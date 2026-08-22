from __future__ import annotations
from game_engine.commands._common import say_chara_line

from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from game_engine.commands._common import favor_trust_proc, global_can, new_source, get_attitude, add_attitude_mes, \
    source_proc
from game_engine.data_pipeline.common_src_modify import common_src_modify

from ...models.shipgirl import ShipGirl

if TYPE_CHECKING:
    from world import World

from .._commands import register_cmd
from .._context import CommandContext


def can(world: World, npc: ShipGirl):
    """执行判定"""
    # 通用判定(气力0 睡眠)
    if not global_can(world.player, npc):
        return False
    # 工作中
    if npc.is_working():
        return False
    # 关系未达到友好
    if npc.get_talent_value("relationship") < 1:
        return False
    # 亲密度不足6
    if npc.abl["intimacy_abl"] < 6:
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

    # 体型差
    temp = 5 * (world.player.get_talent_value('male_body') + 1 - npc.get_talent_value('female_body'))
    score += temp
    mes = add_attitude_mes(mes, f"体型差({temp})")

    # 受虐狂
    if npc.has_talent('masochism'):
        temp = 10
        score += temp
        mes = add_attitude_mes(mes, f"受虐狂({temp})")

    # 秘书舰
    if npc == world.npc_manager.secretary_ship:
        temp = 10
        score += temp
        mes = add_attitude_mes(mes, f"秘书舰({temp})")

    if score >= success_score:
        mes += f"={score}≥{success_score} 成功！"
        ok = True
    else:
        mes += f"={score}<{success_score} 失败！"
        ok = False
    return ok, mes


@register_cmd("push_down", "推倒", "性骚扰", can=can)
def push_down(world: World, option: str):
    """推倒
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    ctx.say(f'尝试推倒{npc.name}！')

    ok, detail = able(world, npc)
    ctx.say(detail)
    say_chara_line(npc, ctx, 'push_down')

    if not ok:
        ctx.say(f"遭到了剧烈反抗……", f"{npc.name}似乎生气了……")
        # TODO: 心情
        source: dict[str, int] = new_source(
            {"escape_source": 1000, "disgust_source": 1200}
        )

        # 通用source修正
        source = common_src_modify(source, npc)
        ctx.say_source(source)

        # source转换过程统一处理
        source_proc(source, world.player, npc, ctx)

        # 体力和气力消耗
        ctx.consume(stamina=100, energy=150, chara=world.player)
        ctx.consume(stamina=125, energy=175, chara=npc)

        # 好感和信赖
        favor_trust_proc(source, npc, ctx)
    else:
        # 开始一场调教
        initiative = {f'{world.player.id}': 100, f'{npc.id}': 0}  # 主导权
        world.train_manager.new_train([world.player.id, npc.id], initiative)

    return ctx.result()
