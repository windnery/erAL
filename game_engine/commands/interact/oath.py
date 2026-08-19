from __future__ import annotations
from game_engine.commands._common import say_chara_line

from typing import TYPE_CHECKING

from config.attr_defs import ATTR_DEFS
from game_engine.commands._common import favor_trust_proc, global_can, new_source, get_attitude, add_attitude_mes, \
    source_proc
from game_engine.data_pipeline.common_src_modify import common_src_modify
from game_engine.data_pipeline.palam.palam_calc import palam_calc

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
    # 关系未达到爱
    if npc.get_talent_value("relationship") < 3:
        return False
    # 亲密度不足9
    if npc.abl["intimacy_abl"] < 9:
        return False
    # 好感度低于1500
    if npc.favor < 1500:
        return False
    # 没有誓约之戒
    if not world.item_manager.has_item("oath_ring"):
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


@register_cmd("oath", "誓约", "日常", can=can)
def oath(world: World, option: str):
    """誓约
    world: 游戏世界对象
    option: 指令对象"""
    ctx = CommandContext(world)
    npc = world.npc_manager.get_npc_by_id(option)
    ctx.say(f'{world.player.name}掏出了事先准备好的誓约之戒，向{npc.name}发起神圣的誓约之邀！')

    ok, detail = able(world, npc)
    say_chara_line(npc, ctx, 'oath')
    ctx.say(detail)

    if not ok:
        ctx.say(f"{npc.name}不知所措，最终还是拒绝了……")
        source: dict[str, int] = new_source(
            {"escape_source": 500, "disgust_source": 1000}
        )
    else:
        ctx.say(f"{npc.name}接受了你的求爱！亲手将戒指戴在了{npc.name}的指尖！")
        ctx.say(f"和{npc.name}的关系变成了[誓约]！")
        ctx.say(f"是时候挑选良辰吉日举办婚礼了！")
        source: dict[str, int] = new_source(
            {
                "love_source": 1000,
                "achievement_source": 500,
                "lust_source": 300,
                "obedience_source": 500,
                "happiness_source": 1000,
            }
        )
        # talent: 誓约
        npc.set_talent("relationship", '4')
        # 消耗誓约之戒
        world.item_manager.use_items("oath_ring")

    # 通用source修正
    source = common_src_modify(source, npc)

    source_list = []
    for k, v in source.items():
        if v != 0:
            source_list.append(f"{ATTR_DEFS['source'][k]['name']}({v})")
    ctx.say(" ".join(source_list))

    # source转换过程统一处理
    source_proc(source, world.player, npc, ctx)

    # 体力和气力消耗
    energy_cost = 100
    ctx.consume(energy=energy_cost, chara=world.player)

    # 好感和信赖
    favor_trust_proc(source, npc, ctx)

    return ctx.result()
